#!/bin/sh -e
apt-get -y install libncurses-dev
[ -e otp_src_R14B03.tar.gz ] || wget http://www.erlang.org/download/otp_src_R14B03.tar.gz
[ -e otp_src_R14B03 ] || tar xzf otp_src_R14B03.tar.gz
cd otp_src_R14B03/
./configure
make
make install
