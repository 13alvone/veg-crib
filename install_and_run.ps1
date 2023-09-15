# Function to handle errors
Function Handle-Error {
    param(
        [int]$line,
        [string]$command
    )
    Write-Host "Error on line $line: $command"
    exit 1
}

# Trap errors
trap {
    Handle-Error $MyInvocation.ScriptLineNumber $_
    exit 1
}

# Check if Docker is installed
if (-Not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Installing Docker..."
    # Download Docker for Windows
    Invoke-WebRequest -Uri "https://download.docker.com/win/stable/Docker%20Desktop%20Installer.exe" -OutFile "$env:TEMP\DockerInstaller.exe"
    # Run the installer
    Start-Process -FilePath "$env:TEMP\DockerInstaller.exe" -Wait
}

# Check if Docker daemon is running
& docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Handle-Error $MyInvocation.ScriptLineNumber "Docker daemon is not running. Please start Docker and try again."
}

# Build the Docker image
Write-Host "Building Docker image..."
& docker build -t veg-crib . -ErrorAction Stop

# Check if the container is already running
$containerId = & docker ps -q --filter "name=veg-crib"
if ($containerId) {
    Write-Host "Stopping existing veg-crib container..."
    & docker stop $containerId -ErrorAction Stop
}

# Run the Docker container
Write-Host "Running Docker container..."
& docker run -p 80:80 --name veg-crib -d veg-crib -ErrorAction Stop
