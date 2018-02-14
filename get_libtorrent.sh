#!/bin/bash
NCPUS=`nproc`
apt-get -y install wget build-essential libboost-system-dev libboost-python-dev libboost-chrono-dev libboost-random-dev libssl-dev 
cd /root
wget https://github.com/arvidn/libtorrent/releases/download/libtorrent-1_1_6/libtorrent-rasterbar-1.1.6.tar.gz
tar -zxf ./libtorrent-rasterbar-1.1.6.tar.gz
cd ./libtorrent-rasterbar-1.1.6

./configure --enable-python-binding --enable-debug=no
make -j$NCPUS
make install
ldconfig
