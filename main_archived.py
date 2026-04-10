import sys
import uselect
import machine
import utime  

led = machine.Pin("LED", machine.Pin.OUT)

poll_obj = uselect.poll()
poll_obj.register(sys.stdin, uselect.POLLIN)

print("PICO_READY") 

pin =  machine.Pin(16, machine.Pin.OUT)

while True:
    if poll_obj.poll(0):
        msg = sys.stdin.readline().strip()
        print("Pico received: " + msg)

        if msg.lower() == "on":
            print("LED is now ON")
            pin.value(1)
        elif msg.lower() == "off":
            print("LED is now OFF")
            pin.value(0)