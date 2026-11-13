#!/usr/bin/env python3
"""
Liste der für die aktuelle Kinowoche gebuchten Werbeeinschaltungen von weischerPLAY holen.
Gibt Name / Playout ID aus und speichert die Liste zusätzlich als JSON.

Pro Kinowoche (Do-Mi) wird das Ergebnis in einer Historie gespeichert. Benachrichtigt (Mail/Signal)
wird nur, wenn die Woche neu ist oder sich die Buchungen gegenüber dem letzten Lauf geändert haben.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

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

def kinowoche(day: date) -> str:
   """Kennung der Kinowoche (Donnerstag bis Mittwoch), benannt nach der ISO-Woche ihres Donnerstags"""
   thursday = day - timedelta(days=(day.weekday() - 3) % 7)
   year, week, _ = thursday.isocalendar()
   return f"{year}-KW{week:02d}"


def load_history(path: Path) -> dict:
   if path.is_file():
      return json.loads(path.read_text())
   return {}


def save_history(path: Path, history: dict) -> None:
   path.write_text(json.dumps(history, indent=2, ensure_ascii=False))


def diff_playouts(old: List[dict], new: List[dict]) -> (List[dict], List[dict]):
   """(hinzugekommen, entfallen), verglichen über die Playout ID"""
   old_ids = {p['playout_id'] for p in old}
   new_ids = {p['playout_id'] for p in new}
   return [p for p in new if p['playout_id'] not in old_ids], [p for p in old if p['playout_id'] not in new_ids]


def write_mail(playouts: List[dict], week: str, changes: Optional[tuple] = None) -> None:
   m = Mailbox()
   pl = "" if len(playouts) == 1 else "en"
   header = f"{len(playouts)} Schlemm Buchung{pl} diese Woche ({week})"
   if changes is not None:
      header = "Update: " + header
   body = """<html lang="de">
   <head><meta charset="UTF-8"><title>Werbung</title></head>
   <body>
   """
   if changes is not None:
      added, removed = changes
      body += "<p>Die Werbe-Buchungen für diese Woche haben sich geändert.</p>"
      if added:
         body += "Neu:<ul>" + "".join(f"<li>{p['name']}</li>" for p in added) + "</ul>"
      if removed:
         body += "Entfallen:<ul>" + "".join(f"<li>{p['name']}</li>" for p in removed) + "</ul>"
   if len(playouts) == 0:
      body += "<p>Nichts zu tun.</p>"
   else:
      body += "Unsere Werbe-Buchungen für diese Woche:<ul>"
      body += "\n".join(f"<li>{playout['name']}</li>" for playout in playouts)
      body += "</ul>"
   body += "Gruß, Ihr Filminsel 🤖</body></html>"
   m.self_mail(header, body)


def send_signal(playouts: List[dict], other: List[str], week: str, changes: Optional[tuple] = None) -> None:
   s = Signal(settings.get('Signal', 'Account'))
   message = ""
   if changes is not None:
      added, removed = changes
      message = f"Update: Die Werbebuchungen für diese Woche ({week}) haben sich geändert.\n"
      if added:
         message += "Neu:\n" + "\n".join(f"+ {p['name']}" for p in added) + "\n"
      if removed:
         message += "Entfallen:\n" + "\n".join(f"- {p['name']}" for p in removed) + "\n"
      message += "\n"
   if len(playouts) > 0:
      message += f"Wir haben diese Woche ({week}) folgende Werbebuchungen:\n"
      message += "\n".join(f"- {playout['name']}" for playout in playouts)
   else:
      message += f"Schlemm hat diese Woche ({week}) keine Werbung."
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
   parser.add_argument('-o', '--output', help='JSON-Datei (Default: %(default)s)')
   parser.add_argument('-m', '--mail', action="store_true", help="Write mail")
   parser.add_argument('-s', '--signal', action="store_true", help="Send Signal message")
   parser.add_argument('--history', type=Path, default=Path('.weischerplay_history.json'),
                       help='Historie der Buchungen je Kinowoche (Default: %(default)s)')
   parser.add_argument('--static', type=Path, required=False, default="", help="Nicht-Weischerplay Werbebuchungen")
   args = parser.parse_args()

   settings = SETTINGS()
   w = Weischerplay()
   try:
      w.login()
      playouts = w.playouts()
   except urllib.error.HTTPError as e:
      sys.exit('weischerPLAY: HTTP {} bei {}'.format(e.code, e.url))

   week = kinowoche(date.today())
   history = load_history(args.history)
   previous = history.get(week)
   if previous is None:
      print(f'Kinowoche {week}: erstmals abgefragt')
      changes = None
   else:
      added, removed = diff_playouts(previous, playouts)
      changes = (added, removed) if added or removed else None
      if changes is None:
         print(f'Kinowoche {week}: keine Änderungen')
      else:
         print(f'Kinowoche {week}: Änderungen ({len(added)} neu, {len(removed)} entfallen)')
         for p in added:
            print('+ {:<48} {}'.format(p['name'], p['playout_id']))
         for p in removed:
            print('- {:<48} {}'.format(p['name'], p['playout_id']))
         print()

   for p in playouts:
      print('{:<50} {}'.format(p['name'], p['playout_id']))

   if args.output:
      with open(args.output, 'w') as f:
         json.dump(playouts, f, indent=2, ensure_ascii=False)

   if previous is None or changes is not None:  # Mail + Signal nur, wenn erster Aufruf oder Änderungen
      other = []
      if args.static.is_file():
         other = args.static.read_text().splitlines()
      if args.mail:
         write_mail(playouts, week, changes)
      if args.signal and settings.has_section("Signal"):
         send_signal(playouts, other, week, changes)
   elif args.signal or args.mail:
      print("Keine Benachrichtigung nötig.")

   # erst nach erfolgreicher Benachrichtigung speichern, damit ein Fehler beim nächsten Lauf erneut meldet
   history[week] = playouts
   save_history(args.history, history)

