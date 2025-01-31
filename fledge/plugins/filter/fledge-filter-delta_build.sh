git clone https://github.com/fledge-iot/fledge-filter-delta.git
cd fledge-filter-delta
chmod +x mkversion
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make
if [ ! -d "${FLEDGE_ROOT}/plugins/filter/delta" ] 
then
    sudo mkdir -p ${FLEDGE_ROOT}/plugins/filter/delta
fi
sudo cp libdelta.so ${FLEDGE_ROOT}/plugins/filter/delta