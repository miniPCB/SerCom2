# Define COM Port Settings
$PortName = "COM3"   # Change to your actual COM port
$BaudRate = 9600     # Adjust as needed
$Parity = "None"
$DataBits = 8
$StopBits = "One"
$Timeout = 1000      # Timeout in milliseconds

# Open Serial Port
$SerialPort = New-Object System.IO.Ports.SerialPort $PortName, $BaudRate, $Parity, $DataBits, $StopBits
$SerialPort.ReadTimeout = $Timeout
$SerialPort.WriteTimeout = $Timeout
$SerialPort.Open()

if (-Not $SerialPort.IsOpen) {
    Write-Host "Failed to open $PortName"
    exit 1
}

Write-Host "Serial port $PortName open. Type hex commands interactively."
Write-Host "Format: 0x00\0x84\0x00\0x00\0x00"
Write-Host "Type 'load' to load commands from file."
Write-Host "Type 'exit' to close connection."

# Function to Convert String Hex Format to Byte Array
function Convert-HexStringToByteArray($hexString) {
    $hexString = $hexString -replace '\\0x', ' '  # Replace '\0x' with space
    $hexString = $hexString.Trim() -replace '"', ''  # Remove quotes
    $hexBytes = $hexString -split ' ' | ForEach-Object { [byte]("0x$_") }
    return $hexBytes
}

# Interactive Loop
while ($true) {
    $UserInput = Read-Host "Enter hex command"

    if ($UserInput -eq "exit") {
        break
    } elseif ($UserInput -eq "load") {
        # Load from commands.txt
        $CommandFile = "commands.txt"
        if (-Not (Test-Path $CommandFile)) {
            Write-Host "Command file not found!"
            continue
        }
        $Commands = Get-Content $CommandFile
        foreach ($Command in $Commands) {
            if ($Command -match 'echo -en "(.*?)"') {
                $HexData = $matches[1]
                $ByteArray = Convert-HexStringToByteArray $HexData
                Write-Host ("Sending: {0} -> [Byte Array] {1}" -f $HexData, ($ByteArray -join ' '))
                $SerialPort.Write($ByteArray, 0, $ByteArray.Length)

                # Read Response
                Start-Sleep -Milliseconds 200
                if ($SerialPort.BytesToRead -gt 0) {
                    $Response = $SerialPort.ReadExisting()
                    Write-Host ("Response: {0}" -f $Response)
                }
            }
        }
    } else {
        # Process User Input
        $ByteArray = Convert-HexStringToByteArray $UserInput
        Write-Host ("Sending: {0} -> [Byte Array] {1}" -f $UserInput, ($ByteArray -join ' '))
        $SerialPort.Write($ByteArray, 0, $ByteArray.Length)

        # Read Response
        Start-Sleep -Milliseconds 200
        if ($SerialPort.BytesToRead -gt 0) {
            $Response = $SerialPort.ReadExisting()
            Write-Host ("Response: {0}" -f $Response)
        }
    }
}

# Close Serial Port
$SerialPort.Close()
Write-Host "Serial communication closed. Exiting..."
