import sys
import subprocess
import importlib
import platform
import shutil
import json
import serial
import serial.tools.list_ports
import datetime
import time

# Function to install packages if missing
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        module = importlib.import_module(import_name)
    except ImportError:
        print(f"⚠ {package} not found. Installing...")

        # Check if running on Raspberry Pi
        if shutil.which("apt") and "raspberrypi" in platform.uname().release:
            try:
                subprocess.check_call(["sudo", "apt", "install", "-y", f"python3-{package.lower()}"])
                module = importlib.import_module(import_name)
            except subprocess.CalledProcessError:
                print(f"⚠ Failed to install {package} via apt. Trying pip instead...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # Import the module again after installation
        module = importlib.import_module(import_name)

    # Store module in global namespace
    globals()[import_name] = module

# Install required packages
required_packages = [("pyserial", "serial"), ("PyQt6", None)]
for package, import_name in required_packages:
    install_and_import(package, import_name)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QComboBox, QLabel, QTextEdit, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QAbstractItemView
)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QTimer

class SerialCommandSender(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Command Sender")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()

        self.port_label = QLabel("Select COM Port:")
        top_layout.addWidget(self.port_label)
        
        self.com_port_combo = QComboBox()
        self.refresh_com_ports()
        top_layout.addWidget(self.com_port_combo)

        self.com_port_refresh_timer = QTimer()
        self.com_port_refresh_timer.timeout.connect(self.refresh_com_ports)
        self.com_port_refresh_timer.start(3000)  # Refresh every 3 seconds

        self.baud_label = QLabel("Select Baud Rate:")
        top_layout.addWidget(self.baud_label)
        
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "115200", "38400", "19200", "57600"])
        self.baud_rate_combo.setCurrentText("9600")
        top_layout.addWidget(self.baud_rate_combo)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        top_layout.addWidget(self.connect_button)

        self.connection_status = QLabel("DISCONNECTED")
        self.update_status_label(False)
        top_layout.addWidget(self.connection_status)

        self.load_json_button = QPushButton("Load JSON Commands")
        self.load_json_button.clicked.connect(self.load_json)
        top_layout.addWidget(self.load_json_button)

        self.load_text_button = QPushButton("Load Text Commands")
        self.load_text_button.clicked.connect(self.load_text)
        top_layout.addWidget(self.load_text_button)

        self.command_list = QListWidget()
        self.command_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.command_list.itemSelectionChanged.connect(self.enable_buttons)
        bottom_layout.addWidget(self.command_list)

        button_layout = QHBoxLayout()
        self.step_button = QPushButton("Send Selected Command")
        self.step_button.setEnabled(False)
        self.step_button.clicked.connect(self.send_selected_command)
        button_layout.addWidget(self.step_button)

        self.fire_all_button = QPushButton("Send All Commands")
        self.fire_all_button.setEnabled(False)
        self.fire_all_button.clicked.connect(self.send_all_commands)
        button_layout.addWidget(self.fire_all_button)

        self.clear_selection_button = QPushButton("Clear Selection")
        self.clear_selection_button.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_selection_button)
        bottom_layout.addLayout(button_layout)
        
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        bottom_layout.addWidget(self.response_area)

        self.save_log_button = QPushButton("Save Log")
        self.save_log_button.clicked.connect(self.save_log)
        bottom_layout.addWidget(self.save_log_button)

        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.serial_connection = None
        self.commands = []
        self.log_data = []
        self.check_connection_timer = QTimer()
        self.check_connection_timer.timeout.connect(self.check_connection)

    def refresh_com_ports(self):
        self.com_port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_port_combo.addItems(ports if ports else ["No COM Ports Found"])

    def send_selected_command(self):
        selected_items = self.command_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.send_command(item.text())

    def send_all_commands(self):
        for command in self.commands:
            self.send_command(command)

    def send_command(self, command):
        if not self.serial_connection:
            self.open_serial_connection()
        if self.serial_connection and self.serial_connection.is_open:
            start_time = time.time()  # Start timing
            try:
                self.serial_connection.write((command + "\r\n").encode())
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode().strip()
                elapsed_time = time.time() - start_time  # Calculate elapsed time
                self.response_area.append(f"[{self.timestamp()}] > {command} (Took {elapsed_time:.3f} sec)\nResponse: {response}\n")
                self.log_data.append({"timestamp": self.timestamp(), "command": command, "response": response, "time": elapsed_time})
            except Exception as e:
                self.response_area.append(f"Error sending command: {e}\n")

    def clear_selection(self):
        """Clears the selection of commands."""
        self.command_list.clearSelection()
        self.enable_buttons()  # Refresh button states

    def toggle_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.update_status_label(False)
            self.connect_button.setText("Connect")
            self.check_connection_timer.stop()
        else:
            self.open_serial_connection()

    def open_serial_connection(self):
        port = self.com_port_combo.currentText()
        baud_rate = int(self.baud_rate_combo.currentText())
        try:
            self.serial_connection = serial.Serial(port, baud_rate, timeout=1)
            self.update_status_label(True)
            self.connect_button.setText("Disconnect")
            self.check_connection_timer.start(1000)
        except Exception as e:
            self.update_status_label(False)
            self.response_area.append(f"Error opening serial connection: {e}\n")

    def check_connection(self):
        if self.serial_connection and not self.serial_connection.is_open:
            self.update_status_label(False)
            self.response_area.append("Device disconnected.\n")
            self.serial_connection = None
            self.connect_button.setText("Connect")
            self.check_connection_timer.stop()

    def save_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "JSON Files (*.json);;Text Files (*.txt)")
        if file_path:
            with open(file_path, "w") as file:
                json.dump(self.log_data, file, indent=4)
            self.response_area.append(f"[{self.timestamp()}] Log saved to {file_path}\n")

    def timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_status_label(self, connected):
        if not hasattr(self, 'log_data'):  # Ensure log_data exists before using it
            self.log_data = []
        event = "Connected to Serial Port" if connected else "Disconnected from Serial Port"
        self.log_data.append({"timestamp": self.timestamp(), "event": event})
        self.com_port_combo.setDisabled(connected)
        self.baud_rate_combo.setDisabled(connected)
        if connected:
            self.connection_status.setText("CONNECTED")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("DISCONNECTED")
            self.connection_status.setStyleSheet("color: red;")

    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                    self.commands = data.get("commands", [])
                    self.command_list.clear()
                    self.command_list.addItems(self.commands)
                    self.response_area.append(f"[{self.timestamp()}] Loaded {len(self.commands)} commands from {file_path}\n")
                    self.log_data.append({"timestamp": self.timestamp(), "event": f"Loaded JSON file: {file_path}"})
                    if self.commands:
                        self.fire_all_button.setEnabled(True)
            except Exception as e:
                self.response_area.append(f"[{self.timestamp()}] Error loading JSON: {e}\n")

    def load_text(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "r") as file:
                    self.commands = [line.strip() for line in file.readlines() if line.strip() and not line.strip().startswith(('#', '//'))]
                    self.command_list.clear()
                    self.command_list.addItems(self.commands)
                    self.response_area.append(f"[{self.timestamp()}] Loaded {len(self.commands)} commands from {file_path}\n")
                    self.log_data.append({"timestamp": self.timestamp(), "event": f"Loaded text file: {file_path}"})
                    if self.commands:
                        self.fire_all_button.setEnabled(True)
            except Exception as e:
                self.response_area.append(f"[{self.timestamp()}] Error loading text file: {e}\n")

    def enable_buttons(self):
        """Enable the send button when at least one command is selected."""
        self.step_button.setEnabled(len(self.command_list.selectedItems()) > 0)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialCommandSender()
    window.show()
    sys.exit(app.exec())