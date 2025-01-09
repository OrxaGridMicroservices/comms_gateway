#!/usr/bin/env bash

##--------------------------------------------------------------------
## Copyright (c) 2020 Dianomic Systems
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##--------------------------------------------------------------------

##
## Author: Mark Riddoch, Akli Rahmoun
##

# Clone the Paho MQTT Python repository
git clone https://github.com/eclipse-paho/paho.mqtt.python
cd paho.mqtt.python

# Install necessary dependencies
cd dependencies
wget https://github.com/ARMmbed/mbedtls/archive/refs/tags/v2.16.12.tar.gz
tar xf v2.16.12.tar.gz
cd ..
mkdir build
cd build
cmake -DBUILD_TESTS=NO -DBUILD_EXAMPLES=NO ..
make
sudo make install
cd ../../..

# Clone the Fledge South MQTT plugin repository
git clone https://github.com/fledge-iot/fledge-south-mqtt.git
cd fledge-south-mqtt-readings

# Set up the build directory and CMake configuration
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..

# Build the plugin
make

# Check if the directory exists, create it if not, and copy the library
if [ ! -d "${FLEDGE_ROOT}/plugins/south/mqtt-reading" ]; then
    sudo mkdir -p $FLEDGE_ROOT/plugins/south/mqtt-readings
fi
sudo cp libpaho.so $FLEDGE_ROOT/plugins/south/mqtt-readings

# Return to the original directory
cd ../../..
