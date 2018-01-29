#!/bin/bash
# main.sh

#Quick mode: do not download/create anything. Reuse the old stuff.
if [ "$1" == "usecache" ]; then
    echo "Will use old lxc images, tmp folder etc."
	export USECACHE=true
	export KEEPTEMPLATES=true
fi

if [ "$1" == "keep" ]; then
    echo "Will keep downloaded templates, tmp folder etc. for later reuse"
	export KEEPTEMPLATES=true
fi

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi


NUMLEECHERS=1
NUMSEEDERS=1
FILESIZE=1024
RUNDURATION=120
LATENCYINTERVALS=50
NUMINTERVALS=10

FILENAME="test.file"
TORRENTNAME="test.torrent"
RESULTFILE="result.csv"
RESULTPLOT="result.png"

TMPFOLDER="tmp/"
SEEDFOLDER=$TMPFOLDER"seeder/"
LEECHFOLDER=$TMPFOLDER"leecher/"

echo "Removing possible previous folder..."
if [[ ! $USECACHE ]]; then
    rm -rf $TMPFOLDER
	echo "Creating temporary folder to conduct tests in..."
	mkdir $TMPFOLDER
	mkdir $SEEDFOLDER
	mkdir $LEECHFOLDER

	echo "Copying leecher and seeder confs"
	cp {seeder.conf,leecher.conf} $TMPFOLDER

	echo "Creating random file of $FILESIZE MiB and torrent for the seeders to seed... This might take a while."
	dd if=/dev/urandom of=$SEEDFOLDER$FILENAME bs=1M count=$FILESIZE status=progress
	ctorrent -t -u 127.0.0.1 -s $SEEDFOLDER$TORRENTNAME $SEEDFOLDER$FILENAME
	cp $SEEDFOLDER$TORRENTNAME $LEECHFOLDER$TORRENTNAME
fi

echo "Copying leecher and seeder scripts to the correct folders..."
cp seeder.py $SEEDFOLDER
cp leecher.py $LEECHFOLDER

echo -e "\n\nRunning container.sh..."
./containers.sh $NUMSEEDERS $RUNDURATION $LATENCYINTERVALS $NUMINTERVALS $RESULTFILE
echo -e "Done running container.sh.\n\n"


echo "Copying data from temporary folder..."
cp $LEECHFOLDER$RESULTFILE $RESULTFILE

echo "Removing temporary folder..."
if [[ ! $KEEPTEMPLATES ]]; then
    rm -rf $TMPFOLDER
fi

echo "Creating plot..."
#python3 create_plot.py $RESULTFILE $RUNDURATION $LATENCYINTERVALS $RESULTPLOT

