#!/bin/bash
cd /srv/dev-disk-by-label-Trailers/neue/sharc
# Alles aelter als 100 Tage
find  . -maxdepth 1 -mtime +100 |xargs -I XX  mv XX /srv/dev-disk-by-label-Trailers/archiv/

