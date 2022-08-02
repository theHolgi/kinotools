import imaplib
import logging
import email

from .settings import SETTINGS


class MAILBOX:
   CONFIGSECTION = 'Email'

   def __init__(self, debuglevel:int = 1):
      config = SETTINGS()
      self.logger = logging.getLogger(self.__class__.__name__)
      self.outdir = config.get(self.CONFIGSECTION, 'Basepath')
      self.M = imaplib.IMAP4_SSL(config.get(self.CONFIGSECTION, 'Host'))
      self.M.debug = debuglevel
      self.M.login(config.get(self.CONFIGSECTION, 'User'), config.get(self.CONFIGSECTION, 'Passwd'))
      self.M.select()

      # copy some IMAP methods
      self.search = self.M.search
      self.fetch = self.M.fetch
      self.store = self.M.store
      self.close = self.M.close

   # TODO: iterator over non-"stored" messages

   def __del__(self):
      self.M.logout()

   def self_mail(self, subject: str, body: str) -> None:
      m = email.message.EmailMessage()
      m['Subject'] = subject
      m['From'] = "robot@filminsel-biblis.de"
      m['To'] = "dcinfo@filminsel-biblis.de"
      m.set_content(body)

      self.M.append('INBOX', None, None, m.as_bytes())
