import unittest
from src.kdm import KDM
from datetime import datetime

class MyTestCase(unittest.TestCase):
   def test_validity(self):
      kdm = KDM.from_file("sample_key1.xml")
      self.assertEqual(kdm.validfrom, datetime.fromisoformat("2022-07-21T22:00:00+00:00"))
      self.assertEqual(kdm.validuntil, datetime.fromisoformat("2022-07-25T01:00:00+00:00"))


if __name__ == '__main__':
   unittest.main()
