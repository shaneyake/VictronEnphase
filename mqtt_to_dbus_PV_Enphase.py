#!/usr/bin/env python3

"""
A class to put a simple service on the dbus, according to victron standards, with constantly updating
paths. See example usage below. It is used to generate dummy data for other processes that rely on the
dbus. See files in dbus_vebus_to_pvinverter/test and dbus_vrm/test for other usage examples.
To change a value while testing, without stopping your dummy script and changing its initial value, write
to the dummy data via the dbus. See example.
https://github.com/victronenergy/dbus_vebus_to_pvinverter/tree/master/test
"""
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import platform
import argparse
import logging
import sys
import os
import paho.mqtt.client as mqtt
import dbus
import dbus.service
# our own packages
#sys.path.insert(1, os.path.join(os.path.dirname(__file__), './ext/velib_python'))
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-modem'))
from vedbus import VeDbusService
 
# Again not all of these needed this is just duplicating the Victron code.
class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)
 
class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)
 
def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()

DBusGMainLoop(set_as_default=True)

MQTT_DATA = {}
dbusservice = {} # Dictonary to hold the multiple services

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("ESS/Enphase/production")
    client.subscribe("ESS/Enphase/kwhLifetime")
    client.subscribe("ESS/Enphase/rmsVoltage")
    client.subscribe("ESS/Enphase/rmsCurrent")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    global dbusservice, MQTT_DATA
    MQTT_DATA[msg.topic] = float(msg.payload.decode(encoding='UTF-8',errors='strict'))

class DbusDummyService(object):
    def __init__(self, servicename, deviceinstance, paths, productname='Enphase', connection='Dummy service'):
        self._dbusservice = VeDbusService(servicename,dbusconnection())
        self._paths = paths

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', 0)
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/FirmwareVersion', 1)
        self._dbusservice.add_path('/HardwareVersion', 1)
        self._dbusservice.add_path('/Connected', 1)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

        GLib.timeout_add(1000, self._update)

    def _update(self):
        global Active_Value, dbusservice
#        print("UPDATE ------------------------------------")
        for path, settings in self._paths.items():
                if 'update' in settings:
 #                   print(path)
                    if settings['update'] in MQTT_DATA:
 #                       print(MQTT_DATA[settings['update']])
                        self._dbusservice[path]=MQTT_DATA[settings['update']]

        return True


    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True # accept the change


# === All code below is to simply run it from the commandline for debugging purposes ===

# It will created a dbus service called com.victronenergy.pvinverter.output.
# To try this on commandline, start this program in one terminal, and try these commands
# from another terminal:
# dbus com.victronenergy.pvinverter.output
# dbus com.victronenergy.pvinverter.output /Ac/Energy/Forward GetValue
# dbus com.victronenergy.pvinverter.output /Ac/Energy/Forward SetValue %20
#
# Above examples use this dbus client: http://code.google.com/p/dbus-tools/wiki/DBusCli
# See their manual to explain the % in %20


def main():
    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)


    logging.basicConfig(level=logging.INFO)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("10.4.4.36", 1883, 60)
    client.loop_start()

    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)


    dbusservice['PV_INVERTER-MQTT1'] = DbusDummyService(
        servicename='com.victronenergy.pvinverter.MQTT1',
        deviceinstance=10,
        paths={
            '/Ac/Energy/Forward':{'initial': None, 'update':"ESS/Enphase/kwhLifetime"},
            '/Ac/Power': {'initial': None, 'update':"ESS/Enphase/production"},
            '/Ac/L1/Current': {'initial': None, 'update':"ESS/Enphase/rmsCurrent"},
            '/Ac/L1/Energy/Forward': {'initial': None, 'update':"ESS/Enphase/kwhLifetime"},
            '/Ac/L1/Power': {'initial': None,'update':"ESS/Enphase/production"},
            '/Ac/L1/Voltage': {'initial': None, 'update':"ESS/Enphase/rmsVoltage"},
            '/Ac/MaxPower': {'initial': 5000},
            '/ErrorCode': {'initial': 0},
            '/Position': {'initial': 1}
#            '/StatusCode': {'initial': 7}
        })

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
