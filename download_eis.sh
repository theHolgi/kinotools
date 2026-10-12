#!/bin/bash
LINK="$1"
USER=Unilever_Kino_2026
PASS=Happiness
wget -v "$1" --no-check-certificate --user="$USER" --password="$PASS"
