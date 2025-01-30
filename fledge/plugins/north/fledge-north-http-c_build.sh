git clone https://github.com/fledge-iot/fledge-north-http-c.git
cd fledge-north-http-c
chmod +x mkversion
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DFLEDGE_INCLUDE=/usr/local/fledge/include/ -DFLEDGE_LIB=/usr/local/fledge/lib/ ..
make
if [ ! -d "${FLEDGE_ROOT}/plugins/north/http-c" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/plugins/north/http-c
fi
sudo cp libhttpc.so $FLEDGE_ROOT/plugins/north/http-c
# Rename the file after copying
sudo mv $FLEDGE_ROOT/plugins/north/http-c/libhttpc.so $FLEDGE_ROOT/plugins/north/http-c/libhttp-c.so