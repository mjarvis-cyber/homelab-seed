import argparse
import json
import paramiko
import subprocess
import re
from ipaddress import ip_network, ip_address

def get_network_info():
    result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
    network_info = result.stdout
    ip_addresses = []
    for line in network_info.splitlines():
        if 'inet ' in line:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line)
            if match:
                ip = match.group(1)
                subnet_mask = int(match.group(2))
                ip_addresses.append((ip, subnet_mask))
    
    return ip_addresses

def find_matching_ip(vm_ipv4, network_info):
    vm_ip = ip_address(vm_ipv4)
    for ip, subnet_mask in network_info:
        network = ip_network(f"{ip}/{subnet_mask}", strict=False)
        if vm_ip in network:
            return ip
    return None

def scp_directory_to_remote(ssh_key, path_to_scp, remote_host, username='ubuntu'):
    key = paramiko.RSAKey(file_obj=ssh_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=username, pkey=key)

    scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    scp.put(path_to_scp, '/tmp/scp-dir', recursive=True)
    scp.close()
    ssh.close()

def run_remote_command(master_ip, agent_name, secret):
    command = f"sudo /home/ubuntu/scp-dir/install.sh -i {master_ip} -p 8080 -n {agent_name} -s {secret}"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(master_ip, username='ubuntu')
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()

def main():
    parser = argparse.ArgumentParser(description='Provision a Jenkins agent.')
    parser.add_argument('--secret-file', required=True, help='Path to the secret file.')
    parser.add_argument('--metadata-file', required=True, help='Path to the VM metadata JSON file.')
    parser.add_argument('--ssh-key-file', required=True, help='Path to the SSH private key file.')
    parser.add_argument('--scp-dir', required=True, help='Path to the directory to SCP.')
    parser.add_argument('--agent-name', required=True, help='Name of the Jenkins agent.')

    args = parser.parse_args()
    with open(args.metadata_file) as f:
        metadata = json.load(f)

    vm_ipv4 = metadata['vm_ipv4']

    with open(args.secret_file) as f:
        secret = f.read().strip()
    network_info = get_network_info()
    master_ip = find_matching_ip(vm_ipv4, network_info)
    if not master_ip:
        print("No matching IP found in the same subnet.")
        return
    with open(args.ssh_key_file) as ssh_key_file:
        scp_directory_to_remote(ssh_key_file, args.scp_dir, master_ip)
    run_remote_command(master_ip, args.agent_name, secret)

if __name__ == "__main__":
    main()
