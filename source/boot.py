# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)



#connect to wifi
import json
import network
import time

def start_network():
    try:
        with open("/config.json", "r") as f:
            config = json.load(f)

        ssid = config["wifi"]["ssid"]
        password = config["wifi"]["password"]

    except (OSError, ValueError, KeyError, TypeError):
        print("Cannot read Wi-Fi settings from /config.json")
        return

    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)

    if not wifi.isconnected():
        print("Connecting to:", ssid)
        wifi.connect(ssid, password)

        start = time.ticks_ms()

        while not wifi.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) >= 20000:
                print("Wi-Fi timeout. Status:", wifi.status())
                return

            time.sleep_ms(100)

    ip = wifi.ifconfig()[0]
    print("Connected. IP address:", ip)

    import webrepl
    webrepl.start()

    print("WebREPL: ws://{}:8266/".format(ip))

#start_network()