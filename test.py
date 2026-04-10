import serial
import time

try:
    ser = serial.Serial('COM5', 115200, timeout=0.1)
    time.sleep(2) # Give the Pico time to start up
    print(" PC Host Online (COM5)")
except Exception as e:
    print(f"Connection Error: {e}")
    exit()
try:
    while True:
        user_input = input("Send to Pico: ")
        
        ser.write((user_input + '\n').encode('utf-8'))
        
        time.sleep(0.1)
        
        while ser.in_waiting > 0:
            pico_reply = ser.readline().decode('utf-8').strip()
            if pico_reply:
                print(f"[PICO]: {pico_reply}")

except KeyboardInterrupt:
    print("\nClosing...")
    ser.close()