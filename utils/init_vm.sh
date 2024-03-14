#!/bin/sh
set -e

if [[ $USER != "outscale" ]];then 
    "This script must be run with outscale user" && exit 1
fi

# check if GITLAB_PASSWORD is set
if [[ -z $GITLAB_PASSWORD ]]; then
    echo "error: GITLAB_PASSWORD environment variable is not set" && exit 1
fi

# check if GITLAB_SSH_PUBLIC_KEY is set
if [[ -z $GITLAB_SSH_PUBLIC_KEY ]]; then
    echo "error: GITLAB_SSH_PUBLIC_KEY environment variable is not set" && exit 1
fi

# update and upgrade apt
echo "info: updating and upgrading apt"
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates \
                    curl \
                    gnupg

# remove docker
echo "info: removing docker"
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove $pkg; 
done

# add docker's official gpg key:
echo "info: adding docker's official gpg key"
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# add the docker repository to apt sources:
echo "info: adding the docker repository to apt sources"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# add nvidia's official gpg key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
&& curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update

# install packages
echo "info: installing packages"
sudo apt install -y python3.10 \
                    python3.10-venv \
                    jq \
                    nvidia-driver-535 \
                    nvidia-cuda-toolkit \
                    nvidia-cuda-toolkit-gcc \
                    nvidia-container-toolkit \
                    fail2ban \
                    docker-ce \
                    docker-ce-cli \
                    containerd.io \
                    docker-buildx-plugin \
                    docker-compose-plugin
# restart docker
echo "info: restarting docker"
sudo systemctl restart docker

# enable and start fail2ban
echo "info: enabling and starting fail2ban"
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# create gitlab user
key=$GITLAB_SSH_PUBLIC_KEY

if [[ $(getent passwd gitlab) ]]; then
    echo "info: user gitlab already exists"
else
    echo "info: creating user gitlab"
    sudo adduser gitlab --gecos "" --uid 1100 --disabled-password
fi

# setting up gitlab user
echo "info: setting up gitlab user"
sudo mkdir -p /home/gitlab/.ssh
echo $key > ~/authorized_keys  && sudo mv ~/authorized_keys /home/gitlab/.ssh
sudo chown -R gitlab:gitlab /home/gitlab/.ssh
sudo chmod 700 /home/gitlab/.ssh
sudo chmod 644 /home/gitlab/.ssh/authorized_keys
(echo $GITLAB_PASSWORD; echo $GITLAB_PASSWORD) | sudo passwd gitlab

# create docker group
echo "info: setting up docker group"
getent group docker 2>&1 > /dev/null || sudo groupadd docker
sudo usermod -aG docker gitlab

# create albert group
echo "info: setting up albert group"
getent group albert 2>&1 > /dev/null || sudo groupadd --gid 1101 albert
sudo usermod -g 1101 gitlab

# create /data folder
echo "info: setting up /data folder"
sudo mkdir -p /data
sudo chgrp -R albert /data
sudo chmod -R 770 /data
