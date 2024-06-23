#!/bin/bash
install_packages="qemu-guest-agent"

echo
if which apt-get &>/dev/null; then
    echo "[+] --- Installing packages '$install_packages'"
    sudo apt update -y
    if ! sudo apt-get install -y --force-yes $install_packages; then
        echo "[!] Could not install packages"
    else
        echo "[=] Packages installed"
        sudo systemctl enable qemu-guest-agent
    fi
elif which yum &>/dev/null; then
    echo "[+] --- Installing packages '$install_packages'"
    if ! sudo yum install -y $install_packages; then
        echo "[!] Could not install packages"
    else
        echo "[=] Packages installed"
        sudo systemctl enable qemu-guest-agent
    fi
elif which zypper &>/dev/null; then
    echo "[+] --- Installing packages '$install_packages'"
    if ! sudo zypper install -y $install_packages; then
        echo "[!] Could not install packages"
    else
        echo "[=] Packages installed"
        sudo systemctl enable qemu-guest-agent
    fi
else
    echo "[!] No compatible package managers detected: could not install '$install_packages'"
fi
