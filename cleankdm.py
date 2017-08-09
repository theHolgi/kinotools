#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os,sys
import xml.etree.ElementTree
from datetime import datetime

dryrun = 0
if len(sys.argv) > 1:
   dryrun = 1

today = datetime.today()

class KDMfile:
   ns = {'kdm': 'http://www.smpte-ra.org/schemas/430-1/2006/KDM',
         'etm': 'http://www.smpte-ra.org/schemas/430-3/2006/ETM',
         'dsig':'http://www.w3.org/2000/09/xmldsig#',
         'enc': 'http://www.w3.org/2001/04/xmlenc#'}
   def __init__(self, filename):
      self._etree = xml.etree.ElementTree.parse(filename)
   def validuntil(self):
      result = self._etree.find('.//kdm:ContentKeysNotValidBefore', KDMfile.ns)
      if result is not None:
         if (result.text.index('T') > 0):
            result = result.text[:result.text.index('T')] # pick only the date
         else:
            print "Unparseable timestamp " + result.text
         return datetime.strptime(result, '%Y-%m-%d')
      else:
         return None

for dirname, dirnames, filenames in os.walk('.'):
   for filename in filenames:
      if filename[-4:] == ".xml":
         filename = os.path.join(dirname, filename)
         e = KDMfile(filename)
         validuntil = e.validuntil()
         if validuntil:
            age = today - validuntil
            if   (age.days < 0): comment=" noch gültig."
            elif (age.days < 7): comment=" gerade abgelaufen."
            else:
               comment = " abgelaufen seit " + str(age.days) + " Tagen. "
               if dryrun == 0:
                  os.unlink(filename)
            print(validuntil.strftime("%Y-%m-%d") + " (" + filename + ") -> " + comment)
