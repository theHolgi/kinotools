import unittest

from src.mailbox import Mailbox
from email.message import EmailMessage
from src.settings import SETTINGS


class MyTestCase(unittest.TestCase):
   def test_mail(self):
      config = SETTINGS()
      msg = EmailMessage()
      msg.set_content("Dies ist ein Test")
      msg['Subject'] = "Ein Test"
      msg['From'] = "external@someone.com"
      msg['To'] = config.get('Email', 'User')
      m = Mailbox()
      m.forward(msg, config.get('Email', 'Notify'))


if __name__ == '__main__':
   unittest.main()
