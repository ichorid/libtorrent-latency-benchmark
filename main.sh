#!/bin/bash
# main.sh


if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

NUMLEECHERS=1
NUMSEEDERS=1
FILESIZE=1024
RUNDURATION=120
STARTINGLATENCY=0
LATENCYINTERVAL=50
NUMINTERVALS=3

FILENAME="test.file"
TORRENTNAME="test.torrent"
RESULTFILE="result.csv"
RESULTPLOT="result.png"

TMPFOLDER="tmp/"
SEEDFOLDER=$TMPFOLDER"seeder/"
LEECHFOLDER=$TMPFOLDER"leecher/"



function tmpdir_clean {
    echo "Removing old ./tmp dir"
    rm -rf $TMPFOLDER
}

function tmpdir_prepare {
	echo "Creating temporary folder to conduct tests in..."
	mkdir $TMPFOLDER
	mkdir $SEEDFOLDER
	mkdir $LEECHFOLDER
	echo "Copying template conf"
	cp template.conf $TMPFOLDER

	echo "Creating random file of $FILESIZE MiB and torrent for the seeders to seed... This might take a while."
	dd if=/dev/urandom of=$SEEDFOLDER$FILENAME bs=1M count=$FILESIZE status=progress
	ctorrent -t -u 127.0.0.1 -s $SEEDFOLDER$TORRENTNAME $SEEDFOLDER$FILENAME
	cp $SEEDFOLDER$TORRENTNAME $LEECHFOLDER$TORRENTNAME
}

function scripts_copy {
    echo "Copying leecher and seeder scripts to the correct folders..."
    cp seeder.py $SEEDFOLDER
    cp leecher.py $LEECHFOLDER
}

function plot_draw {
    echo "Copying data from temporary folder..."
    cp $LEECHFOLDER$RESULTFILE $RESULTFILE
    echo "Creating plot..."
    python3 create_plot.py $RESULTFILE $RESULTPLOT
}


#Quick mode: do not download/create anything. Reuse the old stuff.
if [ "$1" == "runcache" ]; then
    echo "Will use old lxc images, tmp folder etc."
    scripts_copy
    ./containers.sh $NUMSEEDERS $RUNDURATION $LATENCYINTERVAL $NUMINTERVALS $RESULTFILE $STARTINGLATENCY
    plot_draw
fi

if [ "$1" == "prepare" ]; then
    echo "Will prepare and keep downloaded templates, tmp folder etc. for later reuse"
    tmpdir_clean
    tmpdir_prepare
    # When run without arguments, container.sh will just prepare the templates
    ./containers.sh
fi

if [ "$1" == "clean" ]; then
    tmpdir_clean
fi

if [ "$1" == "" ]; then
    tmpdir_clean
    tmpdir_prepare
    scripts_copy
    echo -e "\n\nRunning container.sh..."
    # Prepare templates
    ./containers.sh
    # Run tests
    ./containers.sh $NUMSEEDERS $RUNDURATION $LATENCYINTERVAL $NUMINTERVALS $RESULTFILE $STARTINGLATENCY
    echo -e "Done running container.sh.\n\n"
    plot_draw
    tmpdir_clean
fi


