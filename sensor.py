import network
import socket
import json
import time
import machine
from machine import Pin, WDT

# Watchdog-Timer mit 8 Sekunden Timeout
wdt = WDT(timeout=8000)

# Onboard-LED definieren
led = Pin("LED", Pin.OUT)

# LED für 1 Sekunde einschalten
led.on()
time.sleep(1)
led.off()

# WLAN-Zugangsdaten
SSID = "intruders"
PASSWORD = "2469495890510770"

# WLAN verbinden
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Verbindung wird hergestellt...")
while not wlan.isconnected():
    time.sleep(1)

print("Verbunden! IP-Adresse:", wlan.ifconfig()[0])

# Onboard-Temperatursensor (RP2040)
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

def read_temperature():
    raw_value = sensor_temp.read_u16()
    voltage = raw_value * conversion_factor
    temperature = 27 - (voltage - 0.706) / 0.001721
    return round(temperature, 2)

# Webserver-Funktion mit besserem Fehlerhandling und nicht-blockierendem Socket
def start_server():
    addr = ('0.0.0.0', 80)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port-Reuse aktivieren
    s.bind(addr)
    s.listen(5)  # Bis zu 5 Verbindungen in Warteschlange
    s.settimeout(2)  # Timeout für accept(), verhindert endloses Warten
    print("Webserver läuft auf Port 80")

    while True:
        try:
            wdt.feed()  # Watchdog zurücksetzen
            try:
                conn, addr = s.accept()
                print("Verbindung von", addr)
            except OSError:
                continue  # Kein Client -> Schleife neu starten

            conn.settimeout(2)  # Timeout für recv(), um Hänger zu vermeiden

            try:
                request = conn.recv(1024)  # HTTP-Request empfangen
                print("Anfrage erhalten")
                
                temperature = read_temperature()

                data = {
                    "temperature": temperature,
                    "humidity": "N/A",
                    "status": "ok"
                }
                response_json = json.dumps(data)

                led.on()
                time.sleep(0.1)
                led.off()

                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "\r\n" +
                    response_json
                )
                conn.send(response)

            except OSError as e:
                print("Socket-Fehler:", e)

            finally:
                conn.close()  # Stelle sicher, dass die Verbindung immer geschlossen wird

        except Exception as e:
            print("Unerwarteter Fehler:", e)

# Server starten
start_server()
