# Step 1: Clone the Paho MQTT repository 
git clone https://github.com/eclipse-paho/paho.mqtt.python.git
cd paho.mqtt.python

# Step 2: Install the Paho MQTT library using pip
pip3 install .


python3 -c "import paho.mqtt.client; print('Paho MQTT installed successfully')"


git clone https://github.com/fledge-iot/fledge-south-mqtt.git
cd fledge-south-mqtt

if [ ! -d "${FLEDGE_ROOT}/python/fledge/plugins/south/mqtt-readings" ] 
then
    sudo mkdir -p $FLEDGE_ROOT/python/fledge/plugins/south/mqtt-readings
fi
sudo cp -r python/fledge/plugins/south/mqtt-readings/ $FLEDGE_ROOT/python/fledge/plugins/south