from configparser import ConfigParser
import os
import json
from typing import Any

basedir = os.path.dirname(__file__)

class SETTINGS(ConfigParser):
   settings = basedir + '/../secrets.ini'
   livedata = basedir + '/../.live.json'

   def __init__(self):
      super().__init__()
      self.read(self.settings)
      try:
         with open(self.livedata) as f:
            self.runtime = json.load(f)
      except FileNotFoundError as e:
         self.runtime = {}

   def get_runtime(self, name) -> Any:
      return self.runtime.get(name)

   def set_runtime(self, name, value: Any) -> None:
      self.runtime[name] = value
      with open(self.livedata, "w") as f:
         f.write(json.dumps(self.runtime))

