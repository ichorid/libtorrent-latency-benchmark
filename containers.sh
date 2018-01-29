#!/bin/bash
# containers.sh
STARTIP=3
SUBNET=10.0.3.
DEPENDENCIES=python3-libtorrent

PYTHONVERSION=python3

LEECHERNAME="Leecher0"
CONFIGOPTIONS="-d ubuntu -r xenial -a amd64"
CONTCONFIG="template.conf"

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

echo "Working from temporary directory $(pwd)/tmp..."
cd tmp

function container_template_clean {
    lxc-stop --quiet -n SeederT
    lxc-destroy --quiet -n SeederT
}

function container_template_create {
    cp $CONTCONFIG SeederT.conf
    echo -e "lxc.network.ipv4 = $SUBNET$STARTIP/24" >> SeederT.conf
    echo -e "lxc.mount.entry = $(pwd) mnt none bind 0 0" >> SeederT.conf
    lxc-create --template download -n SeederT --config SeederT.conf -- $CONFIGOPTIONS
    lxc-start -n SeederT

    echo "Installing dependencies on SeederT"
    lxc-attach -n SeederT -- ping -c1 8.8.8.8
    sleep 5
    lxc-attach -n SeederT -- apt-get update
    lxc-attach -n SeederT -- apt-get upgrade -y
    lxc-attach -n SeederT -- apt install $DEPENDENCIES -y
    lxc-stop -n SeederT
}

function containers_cleanall {
    echo "Destroying old containers..."
    lxc-destroy --quiet -n $LEECHERNAME
    for container in "${seeder_container_names[@]}"
    do
        lxc-destroy --quiet -n $container
    done
}

function seeder_containers_names_generate {
    seeder_container_names=()
    for index in `seq 1 $NUMSEEDERS`
    do
        seeder_container_names+=("Seeder$index")
    done
}

function seeders_create {
    echo "Starting seeder containers..."
    ip=$STARTIP
    for container in "${seeder_container_names[@]}"
    do
        echo "Cloning and starting up $container..."
        cp $CONTCONFIG $container.conf
        lxc-copy -e -n SeederT -N $container 
        lxc-attach -n $container -- ifconfig eth0 $SUBNET$ip/24 up
        ((ip++))
    done
    for container in "${seeder_container_names[@]}"
    do
        echo "Starting seeding..."
        lxc-attach -n $container -- /usr/bin/$PYTHONVERSION /mnt/seeder/seeder.py &
    done
}

function leecher_create {
    echo "Creating and starting leecher..."
    lxc-copy -e -n SeederT -N $LEECHERNAME 
    lxc-attach -n $LEECHERNAME -- ifconfig eth0 $SUBNET$((ip+1))/24 up &
}

function benchmark_run {
    echo -e "\nStarting the test..."
    lxc-attach -n $LEECHERNAME -- /usr/bin/$PYTHONVERSION /mnt/leecher/leecher.py $STARTIP $NUMSEEDERS $RUNDURATION $LATENCYINTERVALS $REPETITIONS $RESULTFILE
    echo "Test is done."
}

function seeders_stop {
    for container in "${seeder_container_names[@]}"
    do
        lxc-stop -n $container
    done
}

function leecher_stop {
    lxc-stop --quiet -n $LEECHERNAME
}

function container_template_clean {
	lxc-destroy -n SeederT
}


NUMSEEDERS=$1
RUNDURATION=$2
LATENCYINTERVALS=$3
REPETITIONS=$4
RESULTFILE=$5

if [[ "$#" -eq 0 ]]; then
    echo "Cleaning up and downloading/updating basic container template"
    container_template_clean
    #TODO: iterate through the list of containers to remove old seeders/leechers
    #containers_cleanall
    container_template_create
else
    if [[ "$#" -eq 5 ]]; then
        seeder_containers_names_generate
        seeders_create
        leecher_create
        benchmark_run
        leecher_stop
        seeders_stop

    else
        echo "Illegal number of arguments, give number of seeders, test durations, latencyintervals and repetitions."
        exit 1
    fi

fi


echo "Leaving temporary folder..."
cd ../
