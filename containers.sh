#!/bin/bash
# containers.sh
STARTIP=3
SUBNET=10.0.3.
DEPENDENCIES=python3-libtorrent

PYTHONVERSION=python

LEECHERNAME="Leecher0"
LEECHERIP=2
CONFIGOPTIONS="-d ubuntu -r xenial -a amd64"
CONTCONFIG="template.conf"
#LEECHLIB="tribler"
LEECHLIB="libtorrent"

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
    lxc-attach -n SeederT -- /mnt/get_libtorrent.sh
    lxc-attach -n SeederT -- /mnt/get_tribler.sh
    #lxc-attach -n SeederT -- apt install $DEPENDENCIES -y
    # Delete eth0 config to prevent it from being managed by ifupdown (to prevent DHCP-based problems)
    lxc-attach -n SeederT -- ifdown eth0
    lxc-attach -n SeederT -- sed -i '/auto eth0/d' /etc/network/interfaces
    lxc-attach -n SeederT -- sed -i '/iface eth0 inet dhcp/d' /etc/network/interfaces
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
    for index in `seq 0 $(($NUMSEEDERS-1))`
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
        lxc-copy -e -n SeederT -N $container 
        sleep 2
        lxc-attach -n $container -- ifconfig eth0 $SUBNET$ip/24 up
        ((ip++))
    done
    for container in "${seeder_container_names[@]}"
    do
        echo "Starting seeding..."
        # It is important to use nohup here, because if the command
        # exits inside the container, and it has no terminal to write
        # to, it produces a segfault.
        lxc-attach -n $container -- nohup /usr/bin/$PYTHONVERSION /mnt/seeder/seeder.py &
    done
}

function leecher_create {
    echo "Creating and starting leecher..."
    lxc-copy -e -n SeederT -N $LEECHERNAME 
    sleep 2
    lxc-attach -n $LEECHERNAME -- ifconfig eth0 $SUBNET$LEECHERIP/24 up
}

function benchmark_run {
    echo -e "\nStarting the test..."
    lxc-attach -n $LEECHERNAME -- env PYTHONPATH=/root/tribler /usr/bin/$PYTHONVERSION /mnt/leecher/leecher.py $STARTIP $NUMSEEDERS $RUNDURATION $LATENCYINTERVALS $REPETITIONS $RESULTFILE $STARTINGLATENCY $LEECHLIB
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
STARTINGLATENCY=$6

if [[ "$#" -eq 0 ]]; then
    echo "Cleaning up and downloading/updating basic container template"
    container_template_clean
    #TODO: iterate through the list of containers to remove old seeders/leechers
    #containers_cleanall
    container_template_create
else
    if [[ "$#" -eq 6 ]]; then
        seeder_container_names=()
        seeder_containers_names_generate
        seeders_create
        leecher_create
        sleep 3
        benchmark_run
        leecher_stop
        seeders_stop
    else
        echo "Illegal number of arguments, give number of seeders, test durations, latencyintervals, repetitions and startinglatency"
        exit 1
    fi
fi


echo "Leaving temporary folder..."
cd ../
