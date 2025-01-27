git clone https://github.com/fledge-iot/fledge-filter-python35.git
cd fledge-filter-python35
chmod +x mkversion
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make
if [ ! -d "${FLEDGE_ROOT}/plugins/filter/python35" ] 
then
    sudo mkdir -p ${FLEDGE_ROOT}/plugins/filter/python35
fi
sudo cp libpython35.so ${FLEDGE_ROOT}/plugins/filter/python35