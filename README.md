<h1>No Longer needed as you can create custom PV inverters in NodeRed now</h1>

NodeRed does the HTTP to MQTT on the GX
Import the flow.json into your NodeRed environment.
You will need to get the Installer Password and insert it in the nodered.
![alt text](https://github.com/shaneyake/VictronEnphase/blob/main/nodered_credentials.png?raw=true)

mqtt_to_dbus_PV_Enphase.py does the MQTT to D-Bus commication.
The device will show up in the GX as a PV inverter.

nohup python /data/mqtt_to_dbus_PV_Enphase.py >/dev/null 2>&1 &
![alt text](https://github.com/shaneyake/VictronEnphase/blob/main/nodered_run_script.png?raw=true)
