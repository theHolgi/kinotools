import unittest
from src.kdm import KDM
from datetime import datetime

class MyTestCase(unittest.TestCase):
   def test_validity(self):
      kdm = KDM.from_file("sample_key1.xml")
      self.assertEqual(kdm.validfrom.strftime("%Y-%m-%d %H:%M"), "2022-07-22 00:00")
      self.assertEqual(kdm.validuntil.strftime("%Y-%m-%d %H:%M"), "2022-07-25 03:00")

      title = "DowntonAbbey2_FTR-5_S_DE-XX_DE_71"
      self.assertEqual(kdm.tohtml(), title + "\n<table><tr><td class=\"critical\">Fri 22.07. 00:00</td><td>-</td>" +
         "<td>Mon 25.07. 03:00</td></tr></table>")

   def test_screen_valid(self):
      kdm = KDM.from_file("matching_key.xml")
      kdm.for_screen("IMB-280887")
      self.assertTrue(kdm.valid_for_screen(), "Ist gültig für screen 280887")
      self.assertFalse(kdm.valid_for_screen("SM.DCP2000-207056"), "Nicht gültig für screen 207056")

   def test_screen_invalid(self):
      kdm = KDM.from_file("nonmatching_key.xml")
      kdm.for_screen("IMB-280887")
      self.assertFalse(kdm.valid_for_screen(), "Nicht gültig für screen 280887")
      self.assertTrue(kdm.valid_for_screen("SM.DCP2000-207056"), "Ist gültig für screen 207056")
      self.assertRegexpMatches(kdm.tohtml(), "💥", "Warnung im Text")

if __name__ == '__main__':
   unittest.main()
