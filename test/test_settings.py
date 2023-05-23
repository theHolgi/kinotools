import unittest
from configparser import NoSectionError, NoOptionError

from src.settings import SETTINGS

class TestSettings(unittest.TestCase):
   def test_query_uuids(self):
      settings = SETTINGS()
      # Clear cache
      settings.runtime["uuids"] = []
      settings.add_uuid("567890")
      self.assertFalse(settings.query_uuid("12345678"), "UUID 12345678 is not known")
      self.assertTrue(settings.query_uuid("567890"), "UUID 567890 is known")
      self.assertSetEqual(settings.queried_uuids, {"12345678", "567890"}, "Both have been queried")

   def test_clean_uuids(self):
      settings = SETTINGS()
      # Set cache
      settings.runtime["uuids"] = ["12345678", "567890"]
      self.assertTrue(settings.query_uuid("12345678"), "UUID 12345678 is not known")
      self.assertSetEqual(settings.clean_uuid_cache(), {"567890"}, "UUID 567890 has not been queried")
      self.assertListEqual(settings.runtime["uuids"], ["12345678"], "UUID 567890 is no longer part of the set")

   def test_query_runtime(self):
      """ Query runtime items"""
      settings = SETTINGS()
      settings.set_runtime("key", "some_value")
      self.assertIsNone(settings.get_runtime("unknown_key"))
      self.assertEqual(settings.get_runtime("key"), "some_value", "Value is stored")
      settings2 = SETTINGS()
      self.assertEqual(settings2.get_runtime("key"), "some_value", "Value is persistent")

   def test_query_config(self):
      """ Query config items"""
      settings = SETTINGS()
      with self.assertRaises(NoSectionError):
         settings.get("unknown_section", "some_key")
      with self.assertRaises(NoOptionError):
         settings.get("Email", "unknown_key")