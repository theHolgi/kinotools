#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os, sys
from datetime import datetime
from src.kdm import KDM

dryrun = False
if len(sys.argv) > 1:
   dryrun = True

today = datetime.today()


for dirname, dirnames, filenames in os.walk('.'):
   for filename in filenames:
      if filename[-4:] == ".xml":
         filename = os.path.join(dirname, filename)
         e = KDM.from_file(filename)
         validuntil = e.validuntil
         if validuntil:
            age = today - validuntil
            if age.days < 0:
               comment=" noch gültig."
            elif age.days < 7:
               comment=" gerade abgelaufen."
            else:
               comment = " abgelaufen seit " + str(age.days) + " Tagen. "
               if not dryrun:
                  os.unlink(filename)
            print(validuntil.strftime("%Y-%m-%d") + " (" + filename + ") -> " + comment)
