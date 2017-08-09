#!/usr/bin/python
import os
import imaplib,email
import zipfile
import ConfigParser

outdir = '/srv/dev-disk-by-label-Trailers/neue/Keys'

secretsfile='secrets.ini'
secretssect='Email'
config = ConfigParser.ConfigParser()
config.read(secretsfile)

debuglevel = 0

def debug(msg, lvl=1):
    if debuglevel >= lvl:
        print msg + "\n"

def parse_mail(mail, count=1):
    n = 1
    stored = False
    for part in mail.walk():
       debug("----- part %d (%s) -----------" % (n, part.get_content_type()))
       debug(str(part)[:160] + "...",2)
       if part.get_content_type() in ("application/zip", "application/octet-stream"):
           filename = part.get_filename()         # Content-Disposition: ...
           if filename is None:
               filename =  part.get_param("name")      # Content-Type: application/zip; name=Feature_Keys_1033707_Filminsel_Biblis.zip
           if filename is None:
               debug("Dateiname konnte nicht ermittelt werden",1)
               filename = "attachment.zip"
           filename = "/tmp/msg" + count + "_" + filename
           print ("Speichere attachment: " + str(filename))
           content = part.get_payload(decode = True)
           f = open(filename, "w")
           f.write(content)
           f.close()
           # Now, unzip
           if zipfile.is_zipfile(filename):
              z = zipfile.ZipFile(filename)
              for memberfile in z.namelist():
                 debug("... " + memberfile,0)
                 if (memberfile[-4:].lower() == '.xml'):
                    member = z.extract(memberfile, outdir)
                 else:
                    debug(" Endung "+memberfile[-4:]+" ist kein XML.")
           else:
               print ("Kein ZIP")
           # Aufraeumen
           os.remove(filename)
           stored = True
       n += 1
    return stored

M = imaplib.IMAP4_SSL(config.get(secretssect,'Host'))
M.debug=debuglevel
M.login(config.get(secretssect,'User'), config.get(secretssect,'Passwd'))
M.select()
typ, data = M.search(None, 'ALL')
for num in data[0].split():
    typ, data = M.fetch(num, 'FLAGS')
    flags = imaplib.ParseFlags(data[0])
    if( "KinoStored" in flags):
      debug("-> Nachricht %s schon gespeichert" % (num))
    else:                   
       typ, data = M.fetch(num, '(RFC822)')
       mail = email.message_from_string(data[0][1])
       debug('Message %s Subject:%s' % (num, mail["Subject"]))
#    print 'Message %s Filename:%s\n' % (num, mail.get_filename())
       if parse_mail(mail, count=num):
          debug("Schluessel gespeichert von dieser Nachricht",1)
          M.store(num, '+FLAGS','KinoStored')
M.close()
M.logout()
