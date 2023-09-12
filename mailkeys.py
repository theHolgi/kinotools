#!/usr/bin/python3
import hashlib
import os
import imaplib
import logging
import email
import zipfile
import binascii
from src.settings import SETTINGS
from datetime import datetime
from src.kdm import KDM
from src.mailbox import Mailbox

debuglevel = 1


class MailParser:
   CONFIGSECTION = 'Email'
   SCREENSECTION = 'Screen'

   def __init__(self):
      config = SETTINGS()
      self.logger = logging.getLogger(self.__class__.__name__)
      self.outdir = config.get(self.CONFIGSECTION, 'Basepath')
      self.config = config
      self.M = Mailbox(debuglevel)
      self.dry = False
      self.messages = []

   def dry_run(self):
      self.dry = True

   def add_key(self, key: KDM) -> None:
      """
      Create a message into the log that is worth to send to the user
      :param filename: name of the file
      :param kdm: KDM to announce
      """

      self.messages.append(key)

   def _mail_body(self):
      stylesheet = """.critical { color: red; }
      table { border-width: 2px; border-style: solid; }"""
      return """<html lang="en">
<head><meta charset="UTF-8"><title>Title</title><style>"""+stylesheet+"""</style></head>
<body>
""" + "\n".join(kdm.tohtml() for kdm in self.messages) + "\n</body>\n</html>"

   def _mail_header(self):
      critical = "⚠️" if any(key.criticalfrom() or key.criticaluntil() for key in self.messages) else ""
      nonmatch = "💀 UNGÜLTIG 💀 " if any(not key.valid_for_screen() for key in self.messages) else ""
      count = (str(len(self.messages)) +" ") if len(self.messages) > 1 else ""
      return critical + nonmatch + count + ",".join(set(key.shorttitle for key in self.messages)) + " Schlüssel geladen"

   def mail_report(self) -> None:
      if len(self.messages) > 0:
         self.M.self_mail(self._mail_header(), self._mail_body())

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
            uuid = mail.get('Message-ID')
            if uuid is None:
               uuid = hashlib.sha1(mail.get('From', '').encode())
               uuid.update(mail.get('Date', '').encode())
               uuid.update(mail.get('Subject', '').encode())
               uuid = binascii.hexlify(uuid.digest()).decode()
               self.logger.info("Erstelle eigene uuid: %s" % uuid)
            if uuid is None:
               self.logger.warning("%s: Keine UUID" % num)
            else:
               if self.config.query_uuid(uuid):
                  self.logger.debug("-> Nachricht %s schon prozessiert" % num)
                  continue
               elif not self.dry:
                  self.config.add_uuid(uuid)
            self.logger.info('Ungelesene Nachricht #%s Subject:%s' % (num, mail["Subject"]))
            print(mail["Subject"])
            #    print 'Message %s Filename:%s\n' % (num, mail.get_filename())
            if self.parse_mail(mail, count=num):
               self.logger.info("Schluessel gespeichert von Machricht \"%s\"" % mail["Subject"])
            if "DCP-Download" in mail["Subject"]:
               self.logger.info("%s ist Download mail" % num)
               if not self.dry:
                  self.M.forward(mail, self.config.get(self.CONFIGSECTION, "Notify"))
            if not self.dry:
               self.M.store(num, '+FLAGS', 'KinoStored')
      self.M.close()
      if not self.dry:
         deleted = self.config.clean_uuid_cache()
         self.logger.info("Removed from cache: %s" % deleted)

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
            tmpfile = "/tmp/msg%s_%s" % (count, filename)

            self.logger.info("Speichere attachment: " + tmpfile)
            content = part.get_payload(decode=True)
            with open(tmpfile, "wb") as f:
               f.write(content)
            # Now, unzip
            if zipfile.is_zipfile(tmpfile):
               dirname = self.outdir + "/" + os.path.splitext(os.path.basename(filename))[0]
               if not os.path.exists(dirname):
                  os.mkdir(dirname)
               z = zipfile.ZipFile(tmpfile, mode="r")
               for memberfile in z.namelist():
                  if os.path.exists(dirname + "/" + memberfile):
                     self.logger.info(memberfile + " existiert bereits")
                  else:
                     self.logger.info("... " + memberfile)
                     if memberfile[-4:].lower() == '.xml':
                        member = z.extract(memberfile, dirname)
                        stored = True
                        kdm = KDM.from_file(member)
                        kdm.for_screen(self.config.get(self.SCREENSECTION, 'pattern'))
                        if kdm.validfrom is not None:
                           self.logger.info("Is valid from: %s ... %s" % (kdm.validfrom, kdm.validuntil))
                           self.add_key(kdm)
                     else:
                        self.logger.info(" Endung " + memberfile[-4:] + " ist kein XML.")
               # Aufraeumen
               os.remove(tmpfile)
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
