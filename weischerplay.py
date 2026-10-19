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
from src.settings import SETTINGS
from src.mailbox import Mailbox

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

def write_mail(header: str, body: str) -> None:
   m = Mailbox()
   m.self_mail(header, body)

if __name__ == '__main__':
   parser = ArgumentParser(description='Gebuchte Werbeeinschaltungen der aktuellen Woche von weischerPLAY holen')
   parser.add_argument('-o', '--output', default='weischerplay.json', help='JSON-Datei (Default: %(default)s)')
   parser.add_argument('-m', '--mail', action="store_true", help="Write mail")
   args = parser.parse_args()

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
   if args.mail:
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
      write_mail(header, body)
