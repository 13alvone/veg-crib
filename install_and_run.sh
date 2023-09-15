#!/bin/bash

# Function to handle errors
handle_error() {
  echo "Error on line $1: $2"
  exit 1
}

# Trap errors
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
  echo "Homebrew is not installed. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || handle_error $LINENO "Failed to install Homebrew."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed. Installing Docker via Homebrew..."
  brew install --cask docker || handle_error $LINENO "Failed to install Docker."
fi

# Check if Docker daemon is running
docker info >/dev/null 2>&1
if [[ $? -ne 0 ]]; then
  handle_error $LINENO "Docker daemon is not running. Please start Docker and try again."
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t veg-crib . || handle_error $LINENO "Failed to build Docker image."

# Check if the container is already running
container_id=$(docker ps -q --filter "name=veg-crib")

if [ ! -z "$container_id" ]; then
  echo "Stopping existing veg-crib container..."
  docker stop "$container_id" || handle_error $LINENO "Failed to stop existing container."
fi

# Run the Docker container
echo "Running Docker container..."
docker run -p 80:80 --name veg-crib -d veg-crib || handle_error $LINENO "Failed to run Docker container."
