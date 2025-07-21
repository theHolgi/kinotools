#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os, sys
from datetime import datetime, timezone
from src.kdm import KDM
from argparse import ArgumentParser


def clean_keys(basedir: str, dryrun: bool) -> None:
   today = datetime.now(timezone.utc)
   for dirname, dirnames, filenames in os.walk(basedir):
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

if __name__ == "__main__":
   arg = ArgumentParser()
   arg.add_argument("--dryrun", action="store_true", default=False)
   arg.add_argument("--path", '-p', default=".")
   args = arg.parse_args()
   clean_keys(args.path, args.dryrun)
