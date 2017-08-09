#!/bin/bash
cd /srv/dev-disk-by-label-Trailers/neue/sharc
find  . -maxdepth 1 -mtime +150 |xargs -I XX  mv XX /srv/dev-disk-by-label-Trailers/archiv/

