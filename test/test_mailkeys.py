import unittest
from unittest.mock import patch, Mock
from mailkeys import MailParser

class MockMail(dict):
	def walk(self):
		x = Mock()
		x.get_content_type.return_value = 'text/html'
		yield x
		y = Mock()
		y.get_content_type.return_value = 'application/zip'
		y.get_filename.return_value = 'xyz.zip'
		y.get_payload.return_value = '<secret>KDM</secret>'
		yield y

class MyTestCase(unittest.TestCase):
	def test_scanmail(self):
		def mail_fetcher(num, criterion):
			if criterion == 'FLAGS':
				return 1, [b"FLAGS x\n"]
			if criterion == '(RFC822)':
				return 2, [b"Subject: Mail x\n"]

		with patch("mailkeys.Mailbox") as mailboxclass:
			with patch("mailkeys.email") as emailmock:
				mailbox = Mock()
				mailbox.search.return_value = [1,["4\n5"]]
				mailbox.fetch.side_effect = mail_fetcher
				mailboxclass.return_value = mailbox
				mockmail = MockMail({'Message-ID': '12345678',
								'Subject': 'Key for xyz'})
				emailmock.message_from_bytes.return_value = mockmail
				settings = Mock()
				settings.query_uuid.return_value = False
				m = MailParser(settings)
				attachments = m.run()

		self.assertEqual(len(attachments), 2)

	def test_addkdm(self):
		settings = Mock()
		settings.query_uuid.return_value = False
		# Matching key
		key1 = Mock()
		key1.title = "Key 1"
		key1.valid_for_screen.return_value = True

		# Non-matching key
		key2 = Mock()
		key2.title = "Key 2"
		key2.valid_for_screen.return_value = False
		m = MailParser(settings)
		m.add_key(key1)
		m.add_key(key2)
		self.assertDictEqual(m.titles, {'Key 1': True, 'Key 2': False})

if __name__ == '__main__':
	unittest.main()
