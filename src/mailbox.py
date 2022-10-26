import imaplib
import logging
from email.message import EmailMessage, Message

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
      try:
         self.M.logout()
      except Exception:
         pass

   def self_mail(self, subject: str, body: str) -> None:
      m = EmailMessage()
      m['Subject'] = subject
      m['From'] = "robot@filminsel-biblis.de"
      m['To'] = "dcinfo@filminsel-biblis.de"
      m.set_content(body, 'html')

      self.M.append('INBOX', None, None, m.as_bytes())

   def forward(self, mail: Message, recp: str) -> None:
      self.logger.debug("Writing message to " + recp)
