import requests
import time

PI_HOST = 'http://192.168.19.121:5000/'  #Pi's IP

while True:
    try:
        response = requests.get(PI_HOST)
        print("Sent heartbeat, response:", response.status_code)
    except Exception as e:
        print("Failed to send heartbeat:", e)
    time.sleep(0.5)