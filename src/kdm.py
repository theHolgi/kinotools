from xml.etree.ElementTree import ElementTree
from datetime import datetime
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
         return datetime.fromisoformat(result.text)
      else:
         return None


   @property
   def validuntil(self) -> Optional[datetime]:
      result = self._etree.find('.//kdm:ContentKeysNotValidAfter', KDM.ns)
      if result is not None:
         return datetime.fromisoformat(result.text)
      else:
         return None
