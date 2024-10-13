#!/bin/bash

# Parameters
REGISTRY=$1
REPO_URL=$2
DOCKER_BAKE_FILE=$3
USERNAME=$4
PASSWORD=$5

if ! docker ps > /dev/null 2>&1; then
  echo "Docker is not accessible inside the container."
  exit 1
fi

echo "REGISTRY: ${REGISTRY}"
echo "REPO_URL: ${REPO_URL}"
echo "DOCKER_BAKE_FILE: ${DOCKER_BAKE_FILE}"
echo "USERNAME: ${USERNAME}"

# Ensure all required parameters are provided
if [ -z "$REGISTRY" ] || [ -z "$REPO_URL" ] || [ -z "$DOCKER_BAKE_FILE" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "Missing required arguments. Usage: ./build.sh <REGISTRY> <REPO_URL> <DOCKER_BAKE_FILE> <USERNAME> <PASSWORD>"
  exit 1
fi

echo "Cloning the repository from ${REPO_URL}..."
git clone "${REPO_URL}" repo && cd repo || exit 1

# Login to the Docker registry
echo "${PASSWORD}" | docker login "https://${REGISTRY}" --username "${USERNAME}" --password-stdin

# Create the buildx builder (if not already created)
docker buildx create --use || true

# Build and push the image using docker buildx bake
docker buildx bake -f "${DOCKER_BAKE_FILE}" --push

cd ../ && rm -rf repo
