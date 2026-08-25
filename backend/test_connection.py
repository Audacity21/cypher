import serial
import time

PORT = "COM5"
BAUD_RATE = 115200

print("Connecting to Arduino...")

arduino = serial.Serial(
    port=PORT,
    baudrate=BAUD_RATE,
    timeout=2
)

# UNO R4 resets when the serial connection opens.
time.sleep(2)

# Remove the READY message from the input buffer.
arduino.reset_input_buffer()

message = '{"type":"cmd","id":"001","cmd":"PING"}\n'

print("Sending:")
print(message)

arduino.write(message.encode("utf-8"))

response = arduino.readline().decode("utf-8").strip()

print("Arduino response:")
print(response)

arduino.close()