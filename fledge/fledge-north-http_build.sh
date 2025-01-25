git clone https://github.com/fledge-iot/fledge-north-http.git
cd fledge-north-http

if [ ! -d "${FLEDGE_ROOT}/python/fledge/plugins/north/http_north" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/python/fledge/plugins/north/http_north
fi
sudo cp -r python/fledge/plugins/north/http_north/ $FLEDGE_ROOT/python/fledge/plugins/north
