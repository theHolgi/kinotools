#!/usr/bin/python3
import os
import imaplib
import logging
import email
import zipfile
from src.settings import SETTINGS
from datetime import datetime
from src.kdm import KDM
from src.mailbox import MAILBOX

debuglevel = 1


class MailParser:
   CONFIGSECTION = 'Email'
   def __init__(self):
      config = SETTINGS()
      self.logger = logging.getLogger(self.__class__.__name__)
      self.outdir = config.get(self.CONFIGSECTION, 'Basepath')
      self.M = MAILBOX(debuglevel)
      self.dry = True
      self.messages = []

   def dry_run(self):
      self.dry = True

   def add_kdm_message(self, msg: str) -> None:
      """
      Create a message into the log that is worth to send to the user
      :param msg: Message (string) to send
      """
      self.messages.append(msg)

   def mail_report(self) -> None:
      if len(self.messages) > 0:
         self.M.self_mail("KDM download report", "\n".join(self.messages))

   def run(self) -> None:
      self.logger.info(" ======================== " + datetime.now().isoformat() + " ==========================")
      typ, data = self.M.search(None, 'ALL')
      for num in data[0].split():
         typ, data = self.M.fetch(num, 'FLAGS')
         flags = imaplib.ParseFlags(data[0])
         if "KinoStored" in flags:
            self.logger.debug("-> Nachricht %s schon gespeichert" % num)
         if "KinoStored" not in flags or self.dry:
            typ, data = self.M.fetch(num, '(RFC822)')
            mail = email.message_from_bytes(data[0][1])
            self.logger.info('Ungelesene Nachricht #%s Subject:%s' % (num, mail["Subject"]))
            #    print 'Message %s Filename:%s\n' % (num, mail.get_filename())
            if self.parse_mail(mail, count=num):
               self.logger.info("Schluessel gespeichert von Machricht \"%s\"" % mail["Subject"])
            if not self.dry:
               self.M.store(num, '+FLAGS', 'KinoStored')
      self.M.close()

   def parse_mail(self, mail, count=1) -> bool:
      n = 1
      stored = False
      for part in mail.walk():
         self.logger.debug("----- part %d (%s) -----------" % (n, part.get_content_type()))
         self.logger.debug(str(part)[:160] + "...")
         if part.get_content_type() in ("application/zip", "application/octet-stream", "application/x-zip-compressed"):
            filename = part.get_filename()  # Content-Disposition: ...
            if filename is None:
               filename = part.get_param("name")  # Content-Type: application/zip; name=Feature_Keys_xyz.zip
            if filename is None:
               self.logger.debug("Dateiname konnte nicht ermittelt werden")
               filename = "attachment.zip"
            filename = "/tmp/msg%s_%s" % (count, filename)

            self.logger.info("Speichere attachment: " + filename)
            content = part.get_payload(decode=True)
            with open(filename, "wb") as f:
               f.write(content)
            # Now, unzip
            if zipfile.is_zipfile(filename):
               z = zipfile.ZipFile(filename)
               for memberfile in z.namelist():
                  if os.path.exists(self.outdir + "/" + memberfile):
                     self.logger.info(memberfile + " existiert bereits")
                  else:
                     self.logger.info("... " + memberfile)
                     if memberfile[-4:].lower() == '.xml':
                        member = z.extract(memberfile, self.outdir)
                        stored = True
                        kdm = KDM.from_file(member)
                        if kdm.validfrom is not None:
                           self.logger.info("Is valid from: %s ... %s" % (kdm.validfrom, kdm.validuntil))
                           self.add_kdm_message("KDM %s is valid from %s to %s" % (memberfile, kdm.validfrom.isoformat(), kdm.validuntil.isoformat()))
                     else:
                        self.logger.info(" Endung " + memberfile[-4:] + " ist kein XML.")
               # Aufraeumen
               os.remove(filename)
            else:
               self.logger.info("Kein ZIP")
         n += 1
      return stored



if __name__ == '__main__':
   from argparse import ArgumentParser

   arg = ArgumentParser()
   arg.add_argument('--debug', '-v', help="Debugging", required=False, default=False, action="store_true")
   arg.add_argument('--dry-run', '-d', help="Dry-run", required=False, default=False, action="store_true")
   args = arg.parse_args()
   logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

   parser = MailParser()
   if args.dry_run:
      parser.dry_run()
   parser.run()
   parser.mail_report()
