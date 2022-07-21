#!/bin/bash
cd /srv/trailers/neue
# Alles älter als 100 Tage
find  . sharc -maxdepth 1 -mtime +100 |xargs -I XX  mv XX /srv/trailers/archiv/

