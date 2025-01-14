

git clone https://github.com/fledge-iot/fledge-south-http.git
cd fledge-south-http

if [ ! -d "${FLEDGE_ROOT}/python/fledge/plugins/south/http_south" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/python/fledge/plugins/south/http_south
fi
sudo cp -r python/fledge/plugins/south/http_south/ $FLEDGE_ROOT/python/fledge/plugins/south