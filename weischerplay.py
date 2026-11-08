#!/usr/bin/env python3
"""
Liste der für die aktuelle Kinowoche gebuchten Werbeeinschaltungen von weischerPLAY holen.
Gibt Name / Playout ID aus und speichert die Liste zusätzlich als JSON.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import List

from src.settings import SETTINGS
from src.mailbox import Mailbox
from src.settings import SETTINGS
from src.signal import Signal

AUTH_URL = "https://ae-sl-prod-api-authentication.azurewebsites.net/application/token"
API_URL = "https://ae-sl-prod-api-portal.azurewebsites.net/"
CONFIGSECTION = 'Weischerplay'


class Weischerplay:
   def __init__(self):
      config = SETTINGS()
      self.user = config.get(CONFIGSECTION, 'User')
      self.passwd = config.get(CONFIGSECTION, 'Passwd')
      self.token = None

   def login(self):
      data = urllib.parse.urlencode({'username': self.user, 'password': self.passwd}).encode()
      request = urllib.request.Request(AUTH_URL, data=data,
                                       headers={'Content-Type': 'application/x-www-form-urlencoded'})
      with urllib.request.urlopen(request, timeout=30) as response:
         self.token = json.loads(response.read().decode())['access_token']

   def post(self, endpoint, payload):
      request = urllib.request.Request(API_URL + endpoint, data=json.dumps(payload).encode(),
                                       headers={'Content-Type': 'application/json',
                                                'Accept': 'application/json',
                                                'Authorization': 'Bearer ' + self.token})
      with urllib.request.urlopen(request, timeout=30) as response:
         return json.loads(response.read().decode())

   def playouts(self):
      """Alle Werbeeinschaltungen der aktuellen Kinowoche, über alle Kinos des Accounts"""
      now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
      cinemas = self.post('Cinema/GetCinemas',
                          {'allowPlayout': True, 'allowBookingList': False, 'onlyActiveScreens': True})
      result = []
      for cinema in cinemas:
         for playout in self.post('Playouts/GetPlayouts', {'TechCinemaId': cinema['techCinemaId'], 'Date': now}):
            result.append({'name': playout['annotationText'], 'playout_id': playout['playoutId']})
      return result

def write_mail(playouts) -> None:
   m = Mailbox()
   pl = "" if len(playouts) == 1 else "en"
   header = f"{len(playouts)} Schlemm Buchung{pl} diese Woche"
   if len(playouts) == 0:
      body = "Nichts zu tun."
   else:
      body = """<html lang="en">
   <head><meta charset="UTF-8"><title>Title</title></head>
   <body>Unsere Werbe-Buchungen für diese Woche:<nl><ul>
   """
   body += "\n".join(f"<li>{playout['name']}</lu>" for playout in playouts)
   body += "</ul>Gruß, Ihr Filminsel 🤖</body></html>"
   m.self_mail(header, body)

def send_signal(playouts: List[dict], other: List[str]) -> None:
   s = Signal(settings.get('Signal', 'Account'))
   if len(playouts) > 0:
      message = "Wir haben diese Woche folgende Werbebuchungen:\n"
      message += "\n".join("- {playout['name']}" for playout in playouts)
   else:
      message = "Schlemm hat diese Woche keine Werbung."
   if other:
      message += f"\nAußerdem nicht vergessen:\n"
      message += "\n".join(f"- {name}" for name in other)
   phone = settings.get('Signal', 'WerbungTarget', fallback=None)
   if phone is not None:
      s.send(message, phone)
   group = settings.get('Signal', 'WerbungTargetGroup', fallback=None)
   if group is not None:
      s.sendGroup(message, group)


if __name__ == '__main__':
   parser = ArgumentParser(description='Gebuchte Werbeeinschaltungen der aktuellen Woche von weischerPLAY holen')
   parser.add_argument('-o', '--output', default='weischerplay.json', help='JSON-Datei (Default: %(default)s)')
   parser.add_argument('-m', '--mail', action="store_true", help="Write mail")
   parser.add_argument('-s', '--signal', action="store_true", help="Send Signal message")
   parser.add_argument('--static', type=Path, required=False, default="")
   args = parser.parse_args()

   settings = SETTINGS()
   w = Weischerplay()
   try:
      w.login()
      playouts = w.playouts()
   except urllib.error.HTTPError as e:
      sys.exit('weischerPLAY: HTTP {} bei {}'.format(e.code, e.url))

   for p in playouts:
      print('{:<50} {}'.format(p['name'], p['playout_id']))

   with open(args.output, 'w') as f:
      json.dump(playouts, f, indent=2, ensure_ascii=False)
   other = []
   if args.static.is_file():
      other = args.static.read_text().splitlines()
   if args.mail:
      write_mail(playouts)
   if args.signal and settings.has_section("Signal"):
      send_signal(playouts, other)

