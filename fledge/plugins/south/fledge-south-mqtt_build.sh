# Step 1: Clone the Paho MQTT repository
git clone https://github.com/eclipse-paho/paho.mqtt.python.git
cd paho.mqtt.python

# Step 2: Checkout the specific version (v1.4.0)
git checkout v1.4.0

# Step 3: Install the Paho MQTT library using pip
pip3 install .

# Step 4: Verify the installation
python3 -c "import paho.mqtt.client; print('Paho MQTT installed successfully')"

# Step 5: Clone the fledge-south-mqtt repository
git clone https://github.com/fledge-iot/fledge-south-mqtt.git
cd fledge-south-mqtt

# Step 6: Ensure the Fledge directory exists and copy the plugin
if [ ! -d "${FLEDGE_ROOT}/python/fledge/plugins/south/mqtt-readings" ]; then
    sudo mkdir -p $FLEDGE_ROOT/python/fledge/plugins/south/mqtt-readings
fi
sudo cp -r python/fledge/plugins/south/mqtt-readings/ $FLEDGE_ROOT/python/fledge/plugins/south
