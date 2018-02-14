#!/bin/bash
cd /root/
apt-get -y install python-twisted python-psutil python-apsw python-chardet python-m2crypto python-sponge python-nacl python-configobj python-meliae python-decorator wget xz-utils
wget https://github.com/Tribler/tribler/releases/download/v7.0.0/Tribler-v7.0.0.tar.xz
tar -xf ./Tribler-v7.0.0.tar.xz
