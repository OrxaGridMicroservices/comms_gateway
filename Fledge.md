Fledge is an open-source, scalable framework for managing, processing, and delivering real-time data from devices, sensors, or other sources to applications or cloud platforms. It provides both a GUI and an API for interaction.

**Fledge GUI Overview:**

The Fledge GUI provides an intuitive way to interact with Fledge components such as services, assets, filters, and notifications. Here's how to get started:

1. **Accessing the Fledge GUI**:
    - **URL**: Open your browser and navigate to the Fledge server's IP address and port (usually http://&lt;server_ip&gt;:8081).
    - **Login**: You'll be prompted to log in. The default login is usually admin for both username and password.
2. **Basic Features of the GUI**:
    - **Dashboard**: The dashboard provides an overview of the current system status, including data ingestion, processing, and delivery statistics.
    - **Assets**: View and manage the devices (assets) connected to Fledge, including their configuration and data streams.
    - **Services**: Configure and monitor various Fledge services (such as data ingesting, processing, and delivering).
    - **Filters**: Apply filters to modify or enrich the data that is being ingested.
    - **Notifications**: Set up alerts based on certain conditions or thresholds.
3. **Adding and Managing Assets**:
    - In the "Assets" tab, you can add devices or data sources that will send data to Fledge.
    - Configure the asset's name, type, and other properties, such as the protocol (e.g., MQTT, OPC UA, Modbus) and connection details.
4. **Configuring Services**:
    - Fledge provides several types of services (e.g., South Service for data input, North Service for data output).
    - You can add, edit, and remove services based on your system's needs.
    - For example, you can configure a South service to collect data from an MQTT broker.
5. **Setting Up Filters**:
    - Filters allow you to process or transform data before sending it out of Fledge.
    - Common filters include simple transformations, statistical functions, or threshold-based actions (like sending notifications when a threshold is exceeded).
  
 ![image](https://github.com/user-attachments/assets/d1522bf4-c030-4d1a-89ca-4b0231f4c64c)
     

###

###
