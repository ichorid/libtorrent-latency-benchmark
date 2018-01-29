#!/bin/bash
# containers.sh

STARTIP=3
SUBNET=10.0.3.
DEPENDENCIES=python3-libtorrent

PYTHONVERSION=python3

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

if [[ "$#" -ne 5 ]]; then
    echo "Illegal number of arguments, give number of seeders, test durations, latencyintervals and repetitions."
    exit 1
fi

NUMSEEDERS=$1
LEECHERNAME="Leecher0"
CONFIGOPTIONS="-d ubuntu -r xenial -a amd64"
LEECHERCONFIG="leecher.conf"
SEEDERCONFIG="seeder.conf"

RUNDURATION=$2
LATENCYINTERVALS=$3
REPETITIONS=$4
RESULTFILE=$5

echo "Working from temporary directory $(pwd)/tmp..."
cd tmp

seeder_container_names=()
for index in `seq 1 $NUMSEEDERS`
do
    seeder_container_names+=("Seeder$index")
done

if [[ ! $USECACHE ]]; then
    echo "Destroying old containers..."
    lxc-destroy --quiet -n $LEECHERNAME
    lxc-destroy --quiet -n seedert
    for container in "${seeder_container_names[@]}"
    do
        lxc-destroy --quiet -n $container
    done

    echo "Creating and updating seeder container template"
    cp $SEEDERCONFIG seeder_template.conf
    echo -e "lxc.network.ipv4 = $SUBNET$STARTIP/24" >> seeder_template.conf
    echo -e "lxc.mount.entry = $(pwd) mnt none bind 0 0" >> seeder_template.conf
    #lxc-update-config -c seeder_template.conf
    lxc-create --template download -n seedert --config seeder_template.conf -- $CONFIGOPTIONS
    lxc-start -n seedert

    echo "Installing dependencies on seedert"
    lxc-attach -n seedert -- ping -c1 8.8.8.8
    sleep 5
    lxc-attach -n seedert -- apt-get update
    lxc-attach -n seedert -- apt-get upgrade -y
    lxc-attach -n seedert -- apt install $DEPENDENCIES -y
    lxc-stop -n seedert
fi

echo "Starting seeder containers..."
ip=$STARTIP
for container in "${seeder_container_names[@]}"
do
    echo "Cloning and starting up $container..."
    cp $SEEDERCONFIG $container.conf
    #echo -e "\nlxc.network.ipv4 = $SUBNET$ip/24" >> $container.conf
    #echo -e "\nlxc.mount.entry = $(pwd)/seeder mnt none bind 0 0" >> $container.conf
    # Unfortunately, --rcfile option triggers a segfault in lxc-copy when
    # used with -s option, so we have to add config during lxc-start later
    #lxc-update-config -c .conf
    lxc-copy -e -n seedert -N $container 
    #lxc-start -e $container -N $container 
    lxc-attach -n $container -- ifconfig eth0 $SUBNET$ip/24 up
    ((ip++))
done

echo "Creating and starting leecher..."
#echo -e "\nlxc.mount.entry = $(pwd)/leecher mnt none bind 0 0" >> $LEECHERCONFIG
lxc-copy -e -n seedert -N $LEECHERNAME 
lxc-attach -n $LEECHERNAME -- ifconfig eth0 $SUBNET$((ip+1))/24 up &

for container in "${seeder_container_names[@]}"
do
    echo "Starting seeding..."
    lxc-attach -n $container -- /usr/bin/$PYTHONVERSION /mnt/seeder/seeder.py &
done

echo -e "\nStarting the test..."
lxc-attach -n $LEECHERNAME -- /usr/bin/$PYTHONVERSION /mnt/leecher/leecher.py $STARTIP $NUMSEEDERS $RUNDURATION $LATENCYINTERVALS $REPETITIONS $RESULTFILE
echo "Test is done."

lxc-stop --quiet -n $LEECHERNAME
#lxc-destroy --quiet -n $LEECHERNAME

for container in "${seeder_container_names[@]}"
do
    lxc-stop -n $container
    #lxc-destroy --quiet -n $container
done

if [[ ! $KEEPTEMPLATES ]]; then
	lxc-destroy -n seedert
fi

echo "Leaving temporary folder..."
cd ../

