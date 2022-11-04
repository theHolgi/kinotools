from configparser import ConfigParser
import os
import json
from typing import Any, Set

basedir = os.path.dirname(__file__)


class SETTINGS(ConfigParser):
   settings = basedir + '/../secrets.ini'
   livedata = basedir + '/../.live.json'

   def __init__(self):
      super().__init__()
      try:
         self.read(self.settings)
      except :
         pass
      self.queried_uuids = set()
      try:
         with open(self.livedata) as f:
            self.runtime = json.load(f)
      except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
         self.runtime = {}
      if "uuids" not in self.runtime:
         self.runtime["uuids"] = []

   def get_runtime(self, name) -> Any:
      return self.runtime.get(name)

   def set_runtime(self, name, value: Any) -> None:
      self.runtime[name] = value
      self._save()

   def _save(self) -> None:
      with open(self.livedata, "w") as f:
         f.write(json.dumps(self.runtime))

   def query_uuid(self, uuid: str) -> bool:
      """
      Query if a UUID has already been seen.
      Side-effect: The list of IDs to store can be emptied with the clean_uuid_cache() command.
      All UUIDs _not_ queried here are then going to be deleted.
      :param uuid: UUID to query
      :return: if this is a known ID
      """
      self.queried_uuids.add(uuid)
      return uuid in self.runtime["uuids"]

   def add_uuid(self, uuid: str) -> None:
      if not self.query_uuid(uuid):  # Avoid duplicates and make sure it's not deleted at cleanup
         self.runtime["uuids"].append(uuid)

   def clean_uuid_cache(self) -> Set[str]:
      to_remove = set(self.runtime["uuids"]) - self.queried_uuids
      self._save()
      return to_remove

