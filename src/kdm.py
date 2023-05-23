import re
from datetime import datetime, timezone
from typing import Optional, Union
from lxml import etree

class KDM:
   ns = {'kdm': 'http://www.smpte-ra.org/schemas/430-1/2006/KDM',
         'etm': 'http://www.smpte-ra.org/schemas/430-3/2006/ETM',
         'dsig':'http://www.w3.org/2000/09/xmldsig#',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}

   def __init__(self, tree: etree.ElementTree):
      self._etree = tree

   @classmethod
   def from_file(cls, filename: Union[str, "Path"]):
      return KDM(etree.parse(filename))

   @classmethod
   def from_text(cls, content: str):
      return KDM(etree.XML(content))

   @property
   def validfrom(self) -> Optional[datetime]:
      result = self._etree.find('.//kdm:ContentKeysNotValidBefore', KDM.ns)
      if result is not None:
         return self._parse_timestamp(result.text)
      else:
         return None


   @property
   def validuntil(self) -> Optional[datetime]:
      result = self._etree.find('.//kdm:ContentKeysNotValidAfter', KDM.ns)
      if result is not None:
         return self._parse_timestamp(result.text)
      else:
         return None

   @staticmethod
   def _parse_timestamp(ts: str) -> datetime:
      if ts.index('+') > 0:
         timestamp = datetime.strptime(ts[:ts.index('+')], '%Y-%m-%dT%H:%M:%S')  # pick only the date
         zone = datetime.strptime(ts[ts.index('+'):], '%z').tzinfo
      return timestamp.replace(tzinfo=timezone.utc).astimezone(zone)

   @property
   def shorttitle(self) -> str:
      result = self._etree.find('.//kdm:ContentTitleText', KDM.ns)
      if result is not None:
         try:
            return result.text[:result.text.index('_')]
         except ValueError:
            return result.text
      else:
         return "No title"

   @property
   def title(self) -> str:
      result = self._etree.find('.//kdm:ContentTitleText', KDM.ns)
      if result is not None:
         result = result.text
         m = re.search("_[57]1", result)
         if m:
            result = result[:m.end()]
         return result
      else:
         return "No title"

   def criticalfrom(self) -> bool:
      return self.validfrom.isoweekday() >= 4  # Thursday

   def criticaluntil(self) -> bool:
      return self.validfrom.isocalendar()[1] == self.validuntil.isocalendar()[1]  # Valid on same week - i.e. latest until sunday

   def tohtml(self) -> str:
      return self.title + "\n<table><tr><td" + (' class="critical"' if self.criticalfrom() else '') + \
      ">" + self.validfrom.strftime("%a %d.%m. %H:%M") + "</td><td>-</td><td" + (' class="critical"' if self.criticaluntil() else '') +">" +\
       self.validuntil.strftime("%a %d.%m. %H:%M") + "</td></tr></table>"
