#!/usr/bin/python3

import psutil
from src.settings import SETTINGS
from src.mailbox import Mailbox
import os

basedir = os.path.dirname(__file__)

class DISKWATCH:
   CONFIGSECTION = 'Disk'

   def __init__(self):
      self.settings = SETTINGS()
   def run(self) -> None:
      for disk in ["Features", "Trailers"]:
         hdd = psutil.disk_usage(self.settings.get(self.CONFIGSECTION, disk))
         print("Disk " + disk + " has " + str(hdd.percent) + "% free.")
         if hdd.percent > int(self.settings.get(self.CONFIGSECTION, "threshold")):
            if not self.settings.get_runtime('disk_warn_' + disk):
               self.warn_mail(disk, hdd)
               self.settings.set_runtime('disk_warn_' + disk, 1)
         else:
            if self.settings.get_runtime('disk_warn_' + disk):
               self.settings.set_runtime('disk_warn_' + disk, 0)

   def warn_mail(self, diskname: str, obj):
      m = Mailbox()
      m.self_mail("HDD " + diskname + " läuft über", "Disk " + diskname + " is ganz schön voll. Bitte aufräumen.\n" +
                  "Prozent benutzt: " + str(obj.percent) + " (" + str(obj.free / (1024*1024)) + " MB frei)\n")


if __name__ == '__main__':
   w = DISKWATCH()
   w.run()
