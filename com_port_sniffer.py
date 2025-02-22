import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
if ports:
    print("Available COM Ports:")
    for port in ports:
        print(port.device)
else:
    print("No COM ports found.")
