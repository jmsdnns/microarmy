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

