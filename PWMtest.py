import serial
import time
import machine

def sendMsg(msg:str):
    try:
        port = serial.Serial('COM5', 115200, timeout=0.1)
        port.write((msg + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")

while True:
    time.sleep(1)
    sendMsg("on")
    print("on")
    time.sleep(1)
    sendMsg("off")
    print("off")