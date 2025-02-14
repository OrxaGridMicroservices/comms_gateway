git clone https://github.com/mz-automation/libiec61850.git
cd libiec61850
git checkout v1.5.1
cd third_party/mbedtls
wget https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/v2.28.2.tar.gz
tar xf v2.28.2.tar.gz
mv mbedtls-2.28.2/ mbedtls-2.28
cd ../..
mkdir build
cd build
cmake -DBUILD_TESTS=NO -DBUILD_EXAMPLES=NO ..
sed -i "s/CONFIG_MMS_SORT_NAME_LIST 1/CONFIG_MMS_SORT_NAME_LIST 0/" ./config/stack_config.h # disable alphabetic order, for getNameList (server side).
make
sudo make install
cd ../../..
git clone https://github.com/fledge-power/fledge-south-iec61850.git
cd fledge-south-iec61850
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make
if [ ! -d "${FLEDGE_ROOT}/plugins/south/iec61850" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/plugins/south/iec61850
fi
sudo cp libiec61850.so $FLEDGE_ROOT/plugins/south/iec61850