git clone https://github.com/fledge-iot/fledge-north-http-c.git
cd fledge-north-http-c
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make
if [ ! -d "${FLEDGE_ROOT}/plugins/north/http" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/plugins/north/http
fi
sudo cp libhttp.so $FLEDGE_ROOT/plugins/north/http
