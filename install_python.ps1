# Define Python Installer URL (Modify for the latest version)
$pythonInstallerURL = "https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe"
$pythonInstallerPath = "$env:TEMP\python_installer.exe"

# Check if Python is already installed
$pythonCheck = python --version 2>$null
if ($pythonCheck -match "Python") {
    Write-Host "✔ Python is already installed: $pythonCheck" -ForegroundColor Green
    exit
}

Write-Host "⚠ Python is not installed. Downloading and installing now..." -ForegroundColor Yellow

# Step 1: Download the Python installer
Invoke-WebRequest -Uri $pythonInstallerURL -OutFile $pythonInstallerPath
Write-Host "✔ Python installer downloaded to $pythonInstallerPath" -ForegroundColor Cyan

# Step 2: Install Python silently (Add to PATH enabled)
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Remove-Item $pythonInstallerPath  # Cleanup installer
Write-Host "✔ Python installation complete." -ForegroundColor Green

# Step 3: Refresh Environment Variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine")

# Step 4: Verify Python Installation
$pythonCheck = python --version 2>$null
if ($pythonCheck -match "Python") {
    Write-Host "✔ Python successfully installed: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "❌ Python installation failed. Please install manually." -ForegroundColor Red
}
