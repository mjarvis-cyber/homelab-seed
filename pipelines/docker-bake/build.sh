#!/bin/bash

# Parameters
REGISTRY=$1
REPO_URL=$2
DOCKER_BAKE_FILE=$3
BRANCH=$4
USERNAME=$5
PASSWORD=$6
TAG=$7

# Ensure Docker is accessible
if ! docker ps > /dev/null 2>&1; then
  echo "Docker is not accessible inside the container."
  exit 1
fi

echo "REGISTRY: ${REGISTRY}"
echo "REPO_URL: ${REPO_URL}"
echo "DOCKER_BAKE_FILE: ${DOCKER_BAKE_FILE}"
echo "BRANCH: ${BRANCH}"
echo "USERNAME: ${USERNAME}"
echo "TAG: ${TAG}"

# Ensure all required parameters are provided
if [ -z "$REGISTRY" ] || [ -z "$REPO_URL" ] || [ -z "$DOCKER_BAKE_FILE" ] || [ -z "$BRANCH" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ] || [ -z "$TAG" ]; then
  echo "Missing required arguments. Usage: ./build.sh <REGISTRY> <REPO_URL> <DOCKER_BAKE_FILE> <BRANCH> <USERNAME> <PASSWORD> <TAG>"
  exit 1
fi

# Clone the repository and check out the specific branch
echo "Cloning the repository from ${REPO_URL} (branch: ${BRANCH})..."
git clone --branch "${BRANCH}" "${REPO_URL}" repo && cd repo || exit 1

# Login to the Docker registry
echo "${PASSWORD}" | docker login "https://${REGISTRY}" --username "${USERNAME}" --password-stdin

# Create the buildx builder (if not already created)
docker buildx create --use || true

# Build and push the image using docker buildx bake, overriding the 'tag' variable in the bake file
docker buildx bake -f "${DOCKER_BAKE_FILE}" --set tag=${TAG} --push

# Cleanup
cd ../ && rm -rf repo
