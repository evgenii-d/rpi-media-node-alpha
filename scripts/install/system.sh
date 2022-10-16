#!/bin/bash
script_folder=$(dirname $(realpath $0))
lightdm_config=/etc/lightdm/lightdm.conf

if test $EUID != 0; then
    echo "root required"
    exit
fi

apt update -y
apt upgrade -y
apt install xserver-xorg openbox lightdm vlc ufw \
    build-essential tk-dev libncurses5-dev libncursesw5-dev \
    libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev \
    libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev -y

ufw allow 5000
ufw --force enable
echo "> ufw enabled"

if ! grep -q "dtoverlay=gpio-shutdown" /boot/config.txt; then
    echo "dtoverlay=gpio-shutdown" >>/boot/config.txt
    echo "> gpio-shutdown enabled"
fi

if ! grep -q "gpu_mem=128" /boot/config.txt; then
    echo "gpu_mem=128" >>/boot/config.txt
    echo "> GPU memory: 128"
fi

sed -i "s|#disable_overscan=.*|disable_overscan=1|" /boot/config.txt
sed -i "s|disable_overscan=.*|disable_overscan=1|" /boot/config.txt
echo "> overscan disabled"

sed -i "s|#xserver-command=.*|xserver-command=X -nocursor|" $lightdm_config
sed -i "s|xserver-command=.*|xserver-command=X -nocursor|" $lightdm_config
echo "> cursor disabled"

sed -i "s|#display-setup-script=.*|display-setup-script=xrandr --output HDMI-2 --auto --same-as HDMI-1|" $lightdm_config
sed -i "s|display-setup-script=.*|display-setup-script=xrandr --output HDMI-2 --auto --same-as HDMI-1|" $lightdm_config
echo "> mirror display activated"

sed -i "s|#autologin-user=.*|autologin-user=$(logname)|" $lightdm_config
sed -i "s|autologin-user=.*|autologin-user=$(logname)|" $lightdm_config
echo "> autologin enabled"
