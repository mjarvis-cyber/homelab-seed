#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i <JENKINS_IP> -p <JENKINS_PORT> -n <JENKINS_AGENT_NAME> -s <JENKINS_SECRET>"
    exit 1
}

# Parse command-line arguments
while getopts ":i:p:n:s:" opt; do
    case ${opt} in
        i)
            JENKINS_IP=${OPTARG}
            ;;
        p)
            JENKINS_PORT=${OPTARG}
            ;;
        n)
            JENKINS_AGENT_NAME=${OPTARG}
            ;;
        s)
            JENKINS_SECRET=${OPTARG}
            ;;
        \?)
            echo "Invalid option: -${OPTARG}" >&2
            usage
            ;;
        :)
            echo "Option -${OPTARG} requires an argument." >&2
            usage
            ;;
    esac
done

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or use sudo"
  exit 1
fi

# Check if all required parameters are provided
if [ -z "${JENKINS_IP}" ] || [ -z "${JENKINS_AGENT_NAME}" ] || [ -z "${JENKINS_SECRET}" ]; then
    echo "Error: Missing required arguments."
    usage
fi

# Set default port if not provided
JENKINS_PORT=${JENKINS_PORT:-8080}

# Uninstall existing Docker packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc;
do
    sudo apt-get remove -y $pkg;
done

# Install Docker
sudo apt-get update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker service
sudo systemctl enable --now docker

# Build Jenkins agent Docker image
docker build \
  --build-arg JENKINS_URL=http://$JENKINS_IP:$JENKINS_PORT/ \
  --build-arg JENKINS_AGENT_NAME=$JENKINS_AGENT_NAME \
  --build-arg JENKINS_SECRET=$JENKINS_SECRET \
  -t jenkins-agent:latest /home/ubuntu/agent-configs

# Run Jenkins agent container
docker run -d jenkins-agent:latest
