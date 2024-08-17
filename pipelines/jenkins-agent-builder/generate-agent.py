import argparse
import requests
from requests.auth import HTTPBasicAuth
import json
import xml.etree.ElementTree as ET

def create_agent(jenkins_url, agent_name, username, api_token, label, executors):
    url = f"{jenkins_url}/computer/doCreateItem?name={agent_name}&type=hudson.slaves.DumbSlave"

    json_payload = {
        "name": agent_name,
        "nodeDescription": "Automatically Generated Agent",
        "numExecutors": executors,
        "remoteFS": "/home/jenkins/agent",
        "labelString": label,
        "mode": "EXCLUSIVE",
        "launchers": [
            {
                "stapler-class": "hudson.slaves.JNLPLauncher",
                "$class": "hudson.slaves.JNLPLauncher",
                "workDirSettings": {
                    "disabled": True,
                    "workDirPath": "",
                    "internalDir": "remoting",
                    "failIfWorkDirIsMissing": False
                },
                "tunnel": "",
                "vmargs": "-Xmx1024m"
            }
        ],
        "retentionStrategy": {
            "stapler-class": "hudson.slaves.RetentionStrategy$Always",
            "$class": "hudson.slaves.RetentionStrategy$Always"
        },
        "nodeProperties": {
            "stapler-class-bag": True,
            "hudson-slaves-EnvironmentVariablesNodeProperty": {
                "env": [
                    {"key": "JAVA_HOME", "value": "/docker-java-home"},
                    {"key": "JENKINS_HOME", "value": "/home/jenkins"}
                ]
            },
            "hudson-tools-ToolLocationNodeProperty": {
                "locations": [
                    {"key": "hudson.plugins.git.GitTool$DescriptorImpl@Default", "home": "/usr/bin/git"},
                    {"key": "hudson.model.JDK$DescriptorImpl@JAVA-8", "home": "/usr/bin/java"},
                    {"key": "hudson.tasks.Maven$MavenInstallation$DescriptorImpl@MAVEN-3.5.2", "home": "/usr/bin/mvn"}
                ]
            }
        }
    }

    json_payload = json.dumps(json_payload)

    response = requests.post(
        url,
        data={"json": json_payload},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        auth=HTTPBasicAuth(username, api_token)
    )

    if response.status_code == 200:
        print(f"Successfully created agent {agent_name}")
    else:
        print(f"Failed to create agent {agent_name}: {response.status_code}")
        print(response.text)

def get_agent_secret(jenkins_url, agent_name, username, api_token):
    url = f"{jenkins_url}/computer/{agent_name}/slave-agent.jnlp"
    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, api_token)
    )
    if response.status_code == 200:
        print("Successfully retrieved the secret")
        return response.text
    else:
        print(f"Failed to retrieve agent secret: {response.status_code}")
        print(response.text)
        return None

def extract_secret_from_jnlp(jnlp_content):
    try:
        root = ET.fromstring(jnlp_content)
        secret = root.find('.//argument').text
        return secret
    except Exception as e:
        print(f"Failed to extract secret: {e}")
        return None

def save_secret_to_file(secret, secret_file):
    with open(secret_file, 'w') as f:
        f.write(secret)
    print(f"Secret saved to {secret_file}")

def main():
    parser = argparse.ArgumentParser(description='Create or update a Jenkins agent.')
    parser.add_argument('--jenkins-url', required=True, help='URL of the Jenkins server.')
    parser.add_argument('--agent-name', required=True, help='Name of the Jenkins agent.')
    parser.add_argument('--username', required=True, help='Jenkins username.')
    parser.add_argument('--api-token', required=True, help='Jenkins API token.')
    parser.add_argument('--label', required=True, help='Label for the Jenkins agent.')
    parser.add_argument('--executors', type=int, required=True, help='Number of executors')
    parser.add_argument('--secret-file', required=True, help='Path to file where the secret will be saved.')

    args = parser.parse_args()

    jenkins_url = args.jenkins_url
    agent_name = args.agent_name
    username = args.username
    api_token = args.api_token
    label = args.label
    executors = args.executors
    secret_file = args.secret_file

    create_agent(jenkins_url, agent_name, username, api_token, label, executors)

    jnlp_content = get_agent_secret(jenkins_url, agent_name, username, api_token)

    if jnlp_content:
        secret = extract_secret_from_jnlp(jnlp_content)
        if secret:
            save_secret_to_file(secret, secret_file)

if __name__ == "__main__":
    main()
