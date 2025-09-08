# A-ORT

Connect the Pi and the laptop to the same wifi

In PuTTy, type: raspberrypi.local

name: gokul
password: raspberry1

to get IP:
ping raspgerrypi.local
ctrl+c to stop

To run rover:
ssh gokul@<pi_ip_address>
cd Desktop/
cd backup/
cd rover-code/

source venv/bin/activate

In terminal, run:  python app.py
Then log into IP address provided on terminal on a browser
