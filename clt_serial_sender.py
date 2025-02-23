#!/usr/bin/env python3
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
import threading

# Function to install packages if missing
def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        module = importlib.import_module(import_name)
    except ImportError:
        print(f"⚠ {package} not found. Installing...")
        if shutil.which("apt") and "raspberrypi" in platform.uname().release:
            try:
                subprocess.check_call(["sudo", "apt", "install", "-y", f"python3-{package.lower()}"])
                module = importlib.import_module(import_name)
            except subprocess.CalledProcessError:
                print(f"⚠ Failed to install {package} via apt. Trying pip instead...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        module = importlib.import_module(import_name)
    globals()[import_name] = module

# Ensure required packages are installed
install_and_import("pyserial", "serial")
install_and_import("prompt_toolkit")

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

class SerialCommandSenderCLI:
    def __init__(self):
        self.echo_enabled = False  # Echo mode off by default
        self.serial_connection = None
        self.commands = []
        self.log_data = []
        self.port = None
        self.baud_rate = 9600  # default baud rate
        self.serial_thread = None

    def timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def list_com_ports(self):
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No COM ports found.")
            return []
        print("Available COM Ports:")
        for idx, port in enumerate(ports):
            print(f"  {idx}: {port.device} - {port.description}")
        return ports

    def open_serial_connection(self):
        if not self.port:
            print("No valid COM port set. Use 'setport' command.")
            return
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"[{self.timestamp()}] Connected to {self.port} at {self.baud_rate} baud.")
            self.log_data.append({"timestamp": self.timestamp(), "event": f"Connected to {self.port}"})
            # Start background thread to poll for incoming serial data
            self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.serial_thread.start()
        except Exception as e:
            print(f"[{self.timestamp()}] Error opening serial connection: {e}")

    def close_serial_connection(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print(f"[{self.timestamp()}] Disconnected from {self.port}.")
            self.log_data.append({"timestamp": self.timestamp(), "event": f"Disconnected from {self.port}"})
            self.serial_connection = None

    def serial_read_loop(self):
        while self.serial_connection and self.serial_connection.is_open:
            try:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting).decode(errors='ignore').strip()
                    if data:
                        print(f"[{self.timestamp()}] Received: {data}")
                        if self.echo_enabled:
                            self.serial_connection.write((data + "\r\n").encode())
                            print(f"[{self.timestamp()}] Echoed: {data}")
            except Exception as e:
                print(f"[{self.timestamp()}] Error reading serial data: {e}")
            time.sleep(0.1)  # Poll every 100 ms

    def toggle_echo(self):
        self.echo_enabled = not self.echo_enabled
        status = "ON" if self.echo_enabled else "OFF"
        print(f"[{self.timestamp()}] Echo mode: {status}")

    def load_json(self, file_path):
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.commands = data.get("commands", [])
                print(f"[{self.timestamp()}] Loaded {len(self.commands)} commands from {file_path}")
                self.log_data.append({"timestamp": self.timestamp(), "event": f"Loaded JSON file: {file_path}"})
        except Exception as e:
            print(f"[{self.timestamp()}] Error loading JSON: {e}")

    def load_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                self.commands = [line.strip() for line in file.readlines()
                                 if line.strip() and not line.strip().startswith(('#', '//'))]
                print(f"[{self.timestamp()}] Loaded {len(self.commands)} commands from {file_path}")
                self.log_data.append({"timestamp": self.timestamp(), "event": f"Loaded text file: {file_path}"})
        except Exception as e:
            print(f"[{self.timestamp()}] Error loading text file: {e}")

    def list_commands(self):
        if not self.commands:
            print("No commands loaded.")
            return
        print("Loaded commands:")
        for idx, command in enumerate(self.commands):
            print(f"  {idx}: {command}")

    def send_command(self, command):
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial connection is not open. Use the 'connect' command first.")
            return
        try:
            start_time = time.time()
            self.serial_connection.write(command.encode())
            time.sleep(0.1)  # Brief pause to allow response
            response = ""
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode(errors='ignore').strip()
            elapsed_time = time.time() - start_time
            print(f"[{self.timestamp()}] Sent: {command} (Took {elapsed_time:.3f} sec)")
            print(f"Response: {response}")
            self.log_data.append({
                "timestamp": self.timestamp(),
                "command": command,
                "response": response,
                "time": elapsed_time
            })
        except Exception as e:
            print(f"Error sending command: {e}")

    def send_all_commands(self):
        if not self.commands:
            print("No commands loaded.")
            return
        for command in self.commands:
            self.send_command(command)

    def save_log(self, file_path):
        try:
            with open(file_path, "w") as file:
                json.dump(self.log_data, file, indent=4)
            print(f"[{self.timestamp()}] Log saved to {file_path}")
        except Exception as e:
            print(f"Error saving log: {e}")

    def print_help(self):
        print("""
Available commands:
  help                Show this help message.
  ports               List available COM ports.
  setport <port>      Set the COM port (e.g., COM3 or /dev/ttyUSB0).
  setbaud <rate>      Set the baud rate (e.g., 9600).
  connect             Open the serial connection.
  disconnect          Close the serial connection.
  loadjson <file>     Load commands from a JSON file.
  loadtxt <file>      Load commands from a text file.
  list                List loaded commands.
  send <index>        Send the command at the specified index.
  sendall             Send all loaded commands.
  echo                Toggle echo mode on/off.
  savlog <file>       Save log data to a file (in JSON format).
  exit                Exit the application.
        """)

    def run(self):
        # Set up prompt_toolkit session and auto-completer
        base_commands = [
            'help', 'ports', 'setport', 'setbaud', 'connect', 'disconnect',
            'loadjson', 'loadtxt', 'list', 'send', 'sendall', 'echo', 'savlog', 'exit'
        ]
        completer = WordCompleter(base_commands, ignore_case=True)
        session = PromptSession(completer=completer)

        print("Welcome to Serial Command Sender CLI with prompt_toolkit.")
        print("Type 'help' to see available commands.")
        while True:
            try:
                cmd_line = session.prompt(">> ")
            except KeyboardInterrupt:
                continue  # Ctrl+C pressed. Simply restart the prompt.
            except EOFError:
                print("Exiting.")
                break

            if not cmd_line:
                continue

            tokens = cmd_line.split()
            command = tokens[0].lower()
            args = tokens[1:]

            if command == "help":
                self.print_help()
            elif command == "ports":
                self.list_com_ports()
            elif command == "setport":
                if args:
                    self.port = args[0]
                    print(f"COM port set to: {self.port}")
                else:
                    print("Usage: setport <port>")
            elif command == "setbaud":
                if args:
                    try:
                        self.baud_rate = int(args[0])
                        print(f"Baud rate set to: {self.baud_rate}")
                    except ValueError:
                        print("Invalid baud rate.")
                else:
                    print("Usage: setbaud <baud_rate>")
            elif command == "connect":
                self.open_serial_connection()
            elif command == "disconnect":
                self.close_serial_connection()
            elif command == "loadjson":
                if args:
                    self.load_json(args[0])
                else:
                    print("Usage: loadjson <file_path>")
            elif command == "loadtxt":
                if args:
                    self.load_text(args[0])
                else:
                    print("Usage: loadtxt <file_path>")
            elif command == "list":
                self.list_commands()
            elif command == "send":
                if args:
                    try:
                        index = int(args[0])
                        if 0 <= index < len(self.commands):
                            self.send_command(self.commands[index])
                        else:
                            print("Invalid command index.")
                    except ValueError:
                        print("Usage: send <command_index>")
                else:
                    print("Usage: send <command_index>")
            elif command == "sendall":
                self.send_all_commands()
            elif command == "echo":
                self.toggle_echo()
            elif command == "savlog":
                if args:
                    self.save_log(args[0])
                else:
                    print("Usage: savlog <file_path>")
            elif command == "exit":
                self.close_serial_connection()
                print("Exiting.")
                break
            else:
                print("Unknown command. Type 'help' for available commands.")

if __name__ == "__main__":
    cli = SerialCommandSenderCLI()
    cli.run()
