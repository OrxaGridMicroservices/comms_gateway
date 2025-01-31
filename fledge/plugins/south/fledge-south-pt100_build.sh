

git clone https://github.com/fledge-iot/fledge-south-pt100.git
cd fledge-south-pt100

if [ ! -d "${FLEDGE_ROOT}/python/fledge/plugins/south/pt100" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/python/fledge/plugins/south/pt100
fi
sudo cp -r python/fledge/plugins/south/pt100 $FLEDGE_ROOT/python/fledge/plugins/south