import argparse
import requests
from requests.auth import HTTPBasicAuth

def create_agent(jenkins_url, agent_name, username, api_token, label, executors):
    url = f"{jenkins_url}/computer/doCreateItem?name={agent_name}"
    config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
    <slave>
      <name>{agent_name}</name>
      <description>Automatically Provisioned Jenkins Agent</description>
      <remoteFS>/home/jenkins</remoteFS>
      <label>{label}</label>
      <mode>NORMAL</mode>
      <numExecutors>{executors}</numExecutors>
      <retentionStrategy class="hudson.slaves.RetentionStrategy$Always"/>
      <launcher class="hudson.slaves.JNLPLauncher">
        <workingDirectory>/path/to/agent/working/dir</workingDirectory>
      </launcher>
      <vncPort>0</vncPort>
      <udpPort>0</udpPort>
      <installations/>
      <doNotUseCustomWorkspace>false</doNotUseCustomWorkspace>
      <disabled>false</disabled>
    </slave>"""
    
    response = requests.post(
        url,
        data=config_xml,
        headers={'Content-Type': 'application/xml'},
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

    secret = get_agent_secret(jenkins_url, agent_name, username, api_token)

    if secret:
        save_secret_to_file(secret, secret_file)

if __name__ == "__main__":
    main()
