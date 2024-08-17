import argparse
import json
import paramiko
import re
from ipaddress import ip_network, ip_address

def get_network_info(master_ip, ssh_key):
    key = paramiko.RSAKey(file_obj=ssh_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(master_ip, username='ubuntu', pkey=key)
    
    stdin, stdout, stderr = ssh.exec_command('ip addr show')
    network_info = stdout.read().decode()
    ssh.close()
    
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
    put_path=f"/tmp/{path_to_scp}"
    scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    scp.put(f"{path_to_scp}/install.sh", put_path)
    scp.put(f"{path_to_scp}/Dockerfile", put_path)
    scp.close()
    ssh.close()

def run_remote_command(master_ip, agent_name, secret, scp_dir):
    command = f"sudo /tmp/{scp_dir}/install.sh -i {master_ip} -p 8080 -n {agent_name} -s {secret}"
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
    parser.add_argument('--master-ip', required=True, help='IP address of the Jenkins master.')

    args = parser.parse_args()
    with open(args.metadata_file) as f:
        metadata = json.load(f)

    vm_ipv4 = metadata['vm_ipv4']

    with open(args.secret_file) as f:
        secret = f.read().strip()
    network_info = get_network_info(args.master_ip, open(args.ssh_key_file, 'r'))
    master_ip = find_matching_ip(vm_ipv4, network_info)
    if not master_ip:
        print("No matching IP found in the same subnet.")
        return
    with open(args.ssh_key_file) as ssh_key_file:
        scp_directory_to_remote(ssh_key_file, args.scp_dir, master_ip)
    run_remote_command(master_ip, args.agent_name, secret, args.scp_dir)

if __name__ == "__main__":
    main()
