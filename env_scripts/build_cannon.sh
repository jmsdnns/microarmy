#!/bin/sh

### Update
apt-get update 

### Install
apt-get -y install \
    python-dev \
    build-essential \
    autoconf \
    automake \
    libtool \
    uuid-dev \
    git-core \
    mercurial \
    python-pip \
    siege

apt-get install cython
pip install cython

### Build zeromq from source
git clone https://github.com/zeromq/libzmq.git
cd libzmq
git checkout v2.1.0
./autogen.sh
./configure && make && make install
ldconfig
cd ..

### Install pyzmq from source
git clone https://github.com/zeromq/pyzmq.git
cd pyzmq
git checkout v2.0.10
cp setup.cfg.template setup.cfg
python ./setup.py install
cd ..

