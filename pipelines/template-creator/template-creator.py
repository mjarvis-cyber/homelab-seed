import requests
import json
import subprocess
import os

def get_current_vmids():
    vm_metadata = "/etc/pve/.vmlist"
    with open(vm_metadata, 'r') as file:
        data = json.load(file)
    return list(data['ids'].keys())

def pick_vmid(target_id, end_id):
    current_ids = get_current_vmids()
    while target_id in current_ids:
        if target_id == end_id:
            raise Exception("No VM IDs available.")
        target_id += 1
    return target_id

def get_qcow(image_url, qcow_dir, qcow_file, name):
    os.makedirs(qcow_dir, exist_ok=True)
    qcow_path = f"/tmp/{name}.img"
    subprocess.run(["wget", "-O", qcow_path, image_url])
    subprocess.run(["mv", qcow_path, qcow_file])
    subprocess.run(["qemu-img", "resize", qcow_file, "32G"])

def disk_config(vmid, qcow_location):
    subprocess.run(["qm", "importdisk", str(vmid), qcow_location, "local-lvm"])
    subprocess.run(["qm", "set", str(vmid), "-scsihw", "virtio-scsi-pci", "-virtio0", f"local-lvm:vm-{vmid}-disk-0"])
    subprocess.run(["qm", "set", str(vmid), "-serial0", "socket"])
    subprocess.run(["qm", "set", str(vmid), "-boot", "c", "-bootdisk", "virtio0"])

def misc_config(vmid):
    subprocess.run(["qm", "set", str(vmid), "-hotplug", "disk,network,usb"])
    subprocess.run(["qm", "set", str(vmid), "-vga", "qxl"])
    subprocess.run(["qm", "set", str(vmid), "--onboot", "1"])

def create_vm(vmid, name):
    subprocess.run(["qm", "create", str(vmid), "-name", name, "-memory", "1024", "-net0", "virtio,bridge=vmbr0", "-cores", "1", "-sockets", "1"])

def template_resource_pool(vmid, resource_pool):
    subprocess.run(["pvesh", "create", "/pools", "--poolid", resource_pool])

def vm_creation_pipeline(vmid, name, image_url, ssh_keys, qcow_dir, user, password, ip_to_use):
    qcow_file = f"{qcow_dir}/{name}.qcow2"
    get_qcow(image_url, qcow_dir, qcow_file, name)
    create_vm(vmid, name)
    disk_config(vmid, qcow_file)
    misc_config(vmid)
    subprocess.run(["qm", "template", str(vmid)])

def runner(resource_pool_name, name, vmid_start, vmid_end, qcow_dir, ssh_keys, image_location, user, password, ip_to_use):
    vmid = pick_vmid(vmid_start, vmid_end)
    vm_creation_pipeline(vmid, name, image_location, ssh_keys, qcow_dir, user, password, ip_to_use)
    template_resource_pool(vmid, resource_pool_name)

def main():
    with open("config.json", "r") as file:
        config = json.load(file)

    for template_name, template in config['templates'].items():
        ssh_keys_file = f"{template_name}-keys.pub"
        with open(ssh_keys_file, 'w') as file:
            file.write("\n".join(template['ssh_keys']))

        runner(
            config['resource_pool'],
            template_name,
            config['template_start_id'],
            config['template_end_id'],
            config['qcow_dir'],
            ssh_keys_file,
            template['img_url'],
            template['user'],
            template['password'],
            config['temporary_ip']
        )

if __name__ == "__main__":
    main()
