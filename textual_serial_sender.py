#!/usr/bin/env python3
import sys
import json
import serial
import serial.tools.list_ports
import datetime
import time
import threading

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static, ListView, ListItem, Log
from textual.screen import Screen

class SerialCommandSenderApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #header {
        background: $accent;
        color: black;
        padding: 1;
    }
    #controls {
        padding: 1;
        background: $boost;
    }
    #commands {
        border: round $accent;
        height: 20;
        margin: 1;
    }
    #output {
        border: solid gray;
        margin: 1;
        height: auto;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_connection = None
        self.commands = []
        self.log_data = []
        self.echo_enabled = False
        self.serial_thread = None

    def compose(self) -> ComposeResult:
        yield Static("Serial Command Sender", id="header")
        with Horizontal(id="controls"):
            yield Button("List COM Ports", id="list_ports")
            yield Input(placeholder="COM Port", id="port_input")
            yield Input(placeholder="Baud Rate", id="baud_input")
            yield Button("Connect", id="connect")
            yield Button("Toggle Echo", id="echo")
            yield Button("Load JSON", id="load_json")
            yield Button("Load Text", id="load_text")
            yield Button("Save Log", id="save_log")
        # Place the Exit button in its own container to ensure visibility.
        yield Button("Exit", id="exit")
        yield ListView(id="commands")
        with Horizontal():
            yield Button("Send Selected", id="send_selected")
            yield Button("Send All", id="send_all")
            yield Button("Clear Selection", id="clear_selection")
        yield Log(id="output")

    def on_mount(self) -> None:
        self.query_one("#baud_input", Input).value = "9600"

    def get_log_widget(self) -> Log:
        return self.query_one(Log)

    def log_message(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_data.append({"timestamp": timestamp, "message": message})
        self.get_log_widget().write(log_message)

    def action_list_ports(self) -> None:
        ports = list(serial.tools.list_ports.comports())
        port_input = self.query_one("#port_input", Input)
        if not ports:
            self.log_message("No COM ports found.")
            port_input.value = ""
        else:
            ports_str = ", ".join([p.device for p in ports])
            port = ports[0].device
            port_input.value = port
            self.log_message(f"Found ports: {ports_str}. Setting port to {port}.")

    def action_connect(self) -> None:
        btn = self.query_one("#connect", Button)
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.serial_connection = None
            self.log_message("Disconnected.")
            btn.label = "Connect"
        else:
            port = self.query_one("#port_input", Input).value.strip()
            try:
                baud_rate = int(self.query_one("#baud_input", Input).value.strip())
            except ValueError:
                self.log_message("Invalid baud rate.")
                return
            if not port:
                self.log_message("No COM port set.")
                return
            try:
                self.serial_connection = serial.Serial(port, baud_rate, timeout=1)
                self.log_message(f"Connected to {port} at {baud_rate} baud.")
                btn.label = "Disconnect"
                self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
                self.serial_thread.start()
            except Exception as e:
                self.log_message(f"Error connecting: {e}")

    def action_toggle_echo(self) -> None:
        self.echo_enabled = not self.echo_enabled
        status = "ON" if self.echo_enabled else "OFF"
        self.log_message(f"Echo mode: {status}")

    def serial_read_loop(self) -> None:
        while self.serial_connection and self.serial_connection.is_open:
            try:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting).decode(errors='ignore').strip()
                    if data:
                        self.call_from_thread(lambda: self.log_message(f"Received: {data}"))
                        if self.echo_enabled:
                            self.serial_connection.write((data + "\r\n").encode())
                            self.call_from_thread(lambda: self.log_message(f"Echoed: {data}"))
            except Exception as e:
                self.call_from_thread(lambda: self.log_message(f"Error reading serial data: {e}"))
            time.sleep(0.1)

    def action_load_json(self) -> None:
        self.push_screen(FileInputScreen("json"))

    def action_load_text(self) -> None:
        self.push_screen(FileInputScreen("txt"))

    def action_save_log(self) -> None:
        self.push_screen(FileInputScreen("save_log"))

    def action_send_selected(self) -> None:
        list_view = self.query_one("#commands", ListView)
        if list_view.index is None:
            self.log_message("No command selected.")
            return
        item = list_view.get_child_at_index(list_view.index)
        if item:
            command = item._label if hasattr(item, "_label") else item.renderable.plain
            self.send_command(command)

    def action_send_all(self) -> None:
        list_view = self.query_one("#commands", ListView)
        for child in list_view.children:
            if isinstance(child, ListItem):
                command = child._label if hasattr(child, "_label") else child.renderable.plain
                self.send_command(command)

    def action_clear_selection(self) -> None:
        self.query_one("#commands", ListView).index = None

    def send_command(self, command: str) -> None:
        if not (self.serial_connection and self.serial_connection.is_open):
            self.log_message("Not connected.")
            return
        try:
            start_time = time.time()
            self.serial_connection.write(command.encode())
            time.sleep(0.1)
            response = ""
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read(self.serial_connection.in_waiting).decode(errors='ignore').strip()
            elapsed_time = time.time() - start_time
            self.log_message(f"> {command} (Took {elapsed_time:.3f} sec)\nResponse: {response}")
        except Exception as e:
            self.log_message(f"Error sending command: {e}")

    def load_commands_from_file(self, file_path: str, file_type: str) -> None:
        try:
            with open(file_path, "r") as file:
                if file_type == "json":
                    data = json.load(file)
                    self.commands = data.get("commands", [])
                else:
                    self.commands = [line.strip() for line in file.readlines() if line.strip() and not line.strip().startswith(('#', '//'))]
            self.log_message(f"Loaded {len(self.commands)} commands from {file_path}")
            list_view = self.query_one("#commands", ListView)
            list_view.clear()
            for cmd in self.commands:
                item = ListItem(Static(cmd))
                item._label = cmd
                list_view.append(item)
        except Exception as e:
            self.log_message(f"Error loading {file_type} file: {e}")

    def save_log_to_file(self, file_path: str) -> None:
        try:
            with open(file_path, "w") as file:
                json.dump(self.log_data, file, indent=4)
            self.log_message(f"Log saved to {file_path}")
        except Exception as e:
            self.log_message(f"Error saving log: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "list_ports":
            self.action_list_ports()
        elif button_id == "connect":
            self.action_connect()
        elif button_id == "echo":
            self.action_toggle_echo()
        elif button_id == "load_json":
            self.action_load_json()
        elif button_id == "load_text":
            self.action_load_text()
        elif button_id == "save_log":
            self.action_save_log()
        elif button_id == "send_selected":
            self.action_send_selected()
        elif button_id == "send_all":
            self.action_send_all()
        elif button_id == "clear_selection":
            self.action_clear_selection()
        elif button_id == "exit":
            self.exit()

class FileInputScreen(Screen):
    def __init__(self, file_type: str, **kwargs):
        super().__init__(**kwargs)
        self.file_type = file_type

    def compose(self) -> ComposeResult:
        yield Static(f"Enter file path for {self.file_type}:", id="file_prompt")
        yield Input(placeholder="File path...", id="file_path")
        with Horizontal():
            yield Button("OK", id="ok")
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            file_path = self.query_one("#file_path", Input).value.strip()
            self.app.pop_screen()
            if self.file_type in ["json", "txt"]:
                self.app.load_commands_from_file(file_path, self.file_type)
            elif self.file_type == "save_log":
                self.app.save_log_to_file(file_path)
        elif event.button.id == "cancel":
            self.app.pop_screen()

if __name__ == "__main__":
    SerialCommandSenderApp().run()
