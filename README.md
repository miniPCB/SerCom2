# Serial Command Sender

A GUI-based serial command sender built using Python and PyQt6. This tool allows users to send and log serial commands to connected devices. Users can load command sequences from JSON or text files, execute individual or batch commands, and log responses.

## 🚀 Features

Auto-Detection of COM Ports

Serial Connection Management (Connect/Disconnect)

Load Commands from JSON/Text Files

Multi-Selection for Sending Commands

Real-Time Serial Communication Logging

Save Logs as JSON or CSV

Hotkeys for Quick Operations

UI-Freezing Prevention with Background Threads

## 🛠️ Installation

Ensure you have Python 3.8+ installed. Then, run the following commands:

## Clone this repository
git clone https://github.com/miniPCB/SerialCommandSender.git

cd SerialCommandSender

## Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

## Install dependencies
pip install -r requirements.txt

# 📖 Usage

Run the application: python serial_command_sender.py

Loading and Sending Commands

Select a COM Port and Baud Rate.

Click 'Connect' to establish a serial connection.

Load Commands from a JSON or text file.

Select Commands from the list (supports multiple selection).

Click "Send Selected Command" or "Send All Commands".

View real-time responses in the log area.

Click "Save Log" to store responses.

# 📂 File Formats

## JSON Command File

{

  "commands": [

    "COMMAND_1",

    "COMMAND_2",

    "COMMAND_3"

  ]
  
}

## Text Command File (Each line is a command)

COMMAND_1

COMMAND_2

COMMAND_3

Empty lines and comments (#, //) are ignored.

# 🛠️ Known Issues & Improvements

Auto-Refresh COM Ports every few seconds.

Improved UI & Multi-threading for smooth operation.

Better Error Handling for missing COM ports or invalid commands.

# 🤝 Contributing

Fork the repository

Create a feature branch (git checkout -b feature-name)

Commit your changes (git commit -m "Added new feature")

Push to GitHub (git push origin feature-name)

Open a Pull Request

# 📜 License

This project is licensed under the MIT License. See LICENSE for details.

# 👨‍💻 Author

Nolan Manteufel
GitHub: miniPCB
LinkedIn: [YourProfile](https://www.linkedin.com/in/nolanmanteufel/)

# ⭐ Support the Project

If you find this project useful, give it a star ⭐ on GitHub!
