# Kino tools

Im täglichen Leben eines Kinobetreibers gibt es ein paar Aufgaben, die man wegautomatisieren möchte.

Systemvoraussetzungen:
- Python 3.4 (das NAS hat leider keine neuere Version)

## Neue Keys holen

Verleiher senden Schlüssel (KDMs) per Mail. Diese müssen aus der Mail extrahiert und zum Import bereitgelegt werden.

```
0 8,17 * * 1-4 ~/tools/mailkeys.py >> /tmp/mailkeys.log
```

# Transitions bauen
0 5    * * *   ~/tools/make_transition.py ~/Dropbox/DCP/Transition ~/Dropbox/DCP/Transition_erledigt

## Abgelaufene Keys löschen

KDMs, die nicht mehr gültig sind, können gelöscht werden.
```
0 6    * * 1   cd /srv/dev-disk-by-label-Trailers/neue/Keys && ~/tools/cleankdm.py
```

## Alte Trailer archivieren
Trailer, die vor längerer Zeit heruntergeladen wurden, können archiviert werden,
um das Import-Verzeichnis schlank zu halten.

```
0 8    1,15 * *   ~/tools/archive.sh
```
