#!/bin/sh
# Flat: 1998 x 1080
# Scope: 2048 x 858
# Full:  2048 x 1080
# HDTV:  1920 x 1080

IN=~/Dropbox/DCP/Transition
OUT=~/Dropbox/DCP/Transition_erledigt

TRANSITIONDIR=/srv/dev-disk-by-label-Trailers/neue/Transition-`date +%Y%m%d`
# working directories
BASE=/tmp
DOCKERBASE=/data
TMPDIR=$BASE/tmp
DOCKERTMP=$DOCKERBASE/tmp
OUTDIR=$BASE/out
DOCKEROUT=$DOCKERBASE/out
###########################

DOCKERCMD="docker run --rm -v$BASE:$DOCKERBASE opendcp"

umask 0002

# Alle Inputs
if ls $IN/*.tif 2>/dev/null; then
  [ -e $TMPDIR ] && rm -rf $TMPDIR
  [ -e $OUTDIR ] && rm -rf $OUTDIR
  mkdir -p $TMPDIR
  mkdir -p $OUTDIR
  cp -v $IN/*.tif $TMPDIR
  $DOCKERCMD opendcp_j2k -i $DOCKERTMP -o $DOCKERTMP -l 3 -b 50
  #cp silence.mxf $OUTDIR

  for infile in $IN/*.tif; do
    INFILE=`basename $infile`
    NAME="${INFILE%.*}"
    TRANSITIONOUTDIR=$TRANSITIONDIR/$NAME
    J2C=$NAME.j2c
    VIDEO=$NAME.mxf
    DCPNAME="$NAME"_XSN_F_2K_`date +%Y%m%d`_SMPTE
    echo "Mache $DCPNAME"
  
    $DOCKERCMD opendcp_mxf -i $DOCKERTMP/$J2C -o $DOCKEROUT/$VIDEO -p 7
    $DOCKERCMD /bin/sh -c "cd $DOCKEROUT; opendcp_xml --reel $VIDEO -k transitional -i 'Holger Lamm' -t \"$DCPNAME\" -a \"$DCPNAME\""
    mkdir -p $TRANSITIONOUTDIR
    mv -v $OUTDIR/* $TRANSITIONOUTDIR && mv $infile $OUT
  done;
fi;
