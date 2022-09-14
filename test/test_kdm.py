import unittest
from src.kdm import KDM
from datetime import datetime

class MyTestCase(unittest.TestCase):
   def test_validity(self):
      kdm = KDM.from_file("sample_key1.xml")
      self.assertEqual(kdm.validfrom, datetime.fromisoformat("2022-07-21T22:00:00+00:00"))
      self.assertEqual(kdm.validuntil, datetime.fromisoformat("2022-07-25T01:00:00+00:00"))

      title = "DowntonAbbey2_FTR-5_S_DE-XX_DE_71"
      self.assertEqual(kdm.tohtml(), title + "\n<table><tr><td class=\"critical\">Thu 21.07.</td><td>-</td>" +
         "<td >Mon 25.07.</td></tr></table>")


if __name__ == '__main__':
   unittest.main()
