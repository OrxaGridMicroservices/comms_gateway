


git clone https://github.com/eclipse-paho/paho.mqtt.python
cd paho.mqtt/paho.mqtt-python
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
git clone https://github.com/fledge-iot/fledge-south-mqtt.git
cd fledge-south-mqtt/mqtt
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make

if [ ! -d "${FLEDGE_ROOT}/plugins/south/mqtt" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/plugins/south/mqtt
fi
sudo cp libiec104.so $FLEDGE_ROOT/plugins/south/mqtt