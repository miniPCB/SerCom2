import sys
import subprocess
import importlib
import json
import serial
import serial.tools.list_ports
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QComboBox, QLabel, QTextEdit, QFileDialog, QVBoxLayout, QWidget
)

# Function to install packages if missing
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        module = importlib.import_module(import_name)
    except ImportError:
        print(f"⚠ {package} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        module = importlib.import_module(import_name)
    globals()[import_name] = module

# Install required packages
required_packages = [("pyserial", "serial"), ("PyQt6", None)]
for package, import_name in required_packages:
    install_and_import(package, import_name)

class SerialCommandSender(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Command Sender")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        self.port_label = QLabel("Select COM Port:")
        layout.addWidget(self.port_label)
        
        self.com_port_combo = QComboBox()
        self.refresh_com_ports()
        layout.addWidget(self.com_port_combo)

        self.baud_label = QLabel("Select Baud Rate:")
        layout.addWidget(self.baud_label)
        
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "115200", "38400", "19200", "57600"])
        self.baud_rate_combo.setCurrentText("9600")
        layout.addWidget(self.baud_rate_combo)

        self.load_json_button = QPushButton("Load JSON Commands")
        self.load_json_button.clicked.connect(self.load_json)
        layout.addWidget(self.load_json_button)

        self.step_button = QPushButton("Send Next Command")
        self.step_button.setEnabled(False)
        self.step_button.clicked.connect(self.send_next_command)
        layout.addWidget(self.step_button)

        self.fire_all_button = QPushButton("Send All Commands")
        self.fire_all_button.setEnabled(False)
        self.fire_all_button.clicked.connect(self.send_all_commands)
        layout.addWidget(self.fire_all_button)

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        layout.addWidget(self.response_area)

        self.save_log_button = QPushButton("Save Log")
        self.save_log_button.clicked.connect(self.save_log)
        layout.addWidget(self.save_log_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.serial_connection = None
        self.commands = []
        self.current_index = 0
        self.log_data = []  # Store logs

    def refresh_com_ports(self):
        self.com_port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_port_combo.addItems(ports if ports else ["No COM Ports Found"])

    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                    self.commands = data.get("commands", [])
                    self.current_index = 0
                    self.response_area.append(f"[{self.timestamp()}] Loaded {len(self.commands)} commands from {file_path}\n")
                    if self.commands:
                        self.step_button.setEnabled(True)
                        self.fire_all_button.setEnabled(True)
            except Exception as e:
                self.response_area.append(f"[{self.timestamp()}] Error loading JSON: {e}\n")

    def open_serial_connection(self):
        port = self.com_port_combo.currentText()
        baud_rate = int(self.baud_rate_combo.currentText())
        try:
            self.serial_connection = serial.Serial(port, baud_rate, timeout=1)
            self.response_area.append(f"[{self.timestamp()}] Connected to {port} at {baud_rate} baud.\n")
        except Exception as e:
            self.response_area.append(f"[{self.timestamp()}] Error opening serial port: {e}\n")
            self.serial_connection = None

    def send_command(self, command):
        if not self.serial_connection:
            self.open_serial_connection()
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write((command + "\r\n").encode())
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode().strip()
                log_entry = {
                    "timestamp": self.timestamp(),
                    "command": command,
                    "response": response
                }
                self.log_data.append(log_entry)
                self.response_area.append(f"[{log_entry['timestamp']}] > {command}\nResponse: {response}\n")
            except Exception as e:
                self.response_area.append(f"[{self.timestamp()}] Error sending command: {e}\n")

    def send_next_command(self):
        if self.current_index < len(self.commands):
            command = self.commands[self.current_index]
            self.send_command(command)
            self.current_index += 1
        else:
            self.response_area.append(f"[{self.timestamp()}] All commands sent.\n")
            self.step_button.setEnabled(False)

    def send_all_commands(self):
        for command in self.commands:
            self.send_command(command)
        self.response_area.append(f"[{self.timestamp()}] All commands sent.\n")

    def save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "JSON Files (*.json);;Text Files (*.txt)")
        if file_path:
            try:
                if file_path.endswith(".json"):
                    with open(file_path, "w") as file:
                        json.dump(self.log_data, file, indent=4)
                else:
                    with open(file_path, "w") as file:
                        for entry in self.log_data:
                            file.write(f"[{entry['timestamp']}] Command: {entry['command']}\nResponse: {entry['response']}\n\n")
                self.response_area.append(f"[{self.timestamp()}] Log saved to {file_path}\n")
            except Exception as e:
                self.response_area.append(f"[{self.timestamp()}] Error saving log: {e}\n")

    def timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialCommandSender()
    window.show()
    sys.exit(app.exec())
