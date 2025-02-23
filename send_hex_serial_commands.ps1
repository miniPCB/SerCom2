# Define COM Port Settings
$PortName = "COM3"   # Change to your actual COM port
$BaudRate = 9600     # Adjust as needed
$Parity = "None"
$DataBits = 8
$StopBits = "One"
$Timeout = 1000      # Timeout in milliseconds

# Load Commands from File
$CommandFile = "commands.txt"  # Each line contains: echo -en "0x00\0x84\0x00\0x00\0x00"
if (-Not (Test-Path $CommandFile)) {
    Write-Host "Command file not found: $CommandFile"
    exit 1
}

# Open Serial Port
$SerialPort = New-Object System.IO.Ports.SerialPort $PortName, $BaudRate, $Parity, $DataBits, $StopBits
$SerialPort.ReadTimeout = $Timeout
$SerialPort.WriteTimeout = $Timeout
$SerialPort.Open()

if (-Not $SerialPort.IsOpen) {
    Write-Host "Failed to open $PortName"
    exit 1
}

Write-Host "Serial port $PortName open. Sending commands..."

# Function to Convert String Hex Format to Byte Array
function Convert-HexStringToByteArray($hexString) {
    $hexString = $hexString -replace '\\0x', ' '  # Replace '\0x' with space
    $hexString = $hexString.Trim() -replace '"', ''  # Remove quotes
    $hexBytes = $hexString -split ' ' | ForEach-Object { [byte]("0x$_") }
    return $hexBytes
}

# Send Commands
$Commands = Get-Content $CommandFile
foreach ($Command in $Commands) {
    # Extract hex values from the format: echo -en "0x00\0x84\0x00\0x00\0x00"
    if ($Command -match 'echo -en "(.*?)"') {
        $HexData = $matches[1]  # Extracted hex string
        $ByteArray = Convert-HexStringToByteArray $HexData

        Write-Host "Sending: $HexData -> [Byte Array] $($ByteArray -join ' ')"
        $SerialPort.Write($ByteArray, 0, $ByteArray.Length)

        # Optional: Read response if device sends data back
        Start-Sleep -Milliseconds 200  # Allow time for response
        if ($SerialPort.BytesToRead -gt 0) {
            $Response = $SerialPort.ReadExisting()
            Write-Host "Response: $Response"
        }
    }
}

# Close Serial Port
$SerialPort.Close()
Write-Host "Serial communication complete. Port closed."
