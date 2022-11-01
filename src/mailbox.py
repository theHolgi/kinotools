import imaplib
import logging
from email.message import EmailMessage, Message
import smtplib

from .settings import SETTINGS


class Mailbox:
   CONFIGSECTION = 'Email'

   def __init__(self, debuglevel: int = 1):
      config = SETTINGS()
      self.config = config
      self.logger = logging.getLogger(self.__class__.__name__)
      self.outdir = config.get(self.CONFIGSECTION, 'Basepath')
      self.M = imaplib.IMAP4_SSL(config.get(self.CONFIGSECTION, 'ImapHost'))
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
      m['From'] = self.config.get(self.CONFIGSECTION, 'Sender')
      m['To'] = self.config.get(self.CONFIGSECTION, 'User')
      m.set_content(body, 'html')

      self.M.append('INBOX', None, None, m.as_bytes())

   def forward(self, mail: Message, recp: str) -> None:
      self.logger.debug("Writing message to " + recp)
      sender = smtplib.SMTP_SSL(host=self.config.get(self.CONFIGSECTION, 'SmtpHost'))
      sender.login(user=self.config.get(self.CONFIGSECTION, 'User'), password=self.config.get(self.CONFIGSECTION, 'Passwd'))
      # Re-write some fields
      mail['Reply-To'] = mail['From']
      mail.replace_header('From', self.config.get(self.CONFIGSECTION, 'Sender'))
      mail.replace_header('To', recp)
      sender.send_message(mail, from_addr=self.config.get(self.CONFIGSECTION, 'Sender'), to_addrs=recp)
      sender.quit()
