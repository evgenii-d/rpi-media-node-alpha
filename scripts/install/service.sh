#!/bin/bash
scripts_folder=$(dirname $(dirname $(realpath $0)))
script_folder=$(dirname $(realpath $0))
user_services=~/".config/systemd/user"

if test $EUID == 0; then
    echo "run as non-root user"
    exit
fi

# apply correct path
sed -i "s|^ExecStart=.*|ExecStart=$scripts_folder/run_vlc.sh|" $script_folder/vlc_rc.service
sed -i "s|^ExecStart=.*|ExecStart=$scripts_folder/run_app.sh|" $script_folder/media_node.service

chmod +x $scripts_folder/run_vlc.sh
chmod +x $scripts_folder/run_app.sh

loginctl enable-linger $(logname)
mkdir -p ~/.config/systemd/user
cp "$script_folder/vlc_rc.service" "$script_folder/media_node.service" "$user_services"
systemctl --user enable vlc_rc.service
systemctl --user enable media_node.service
echo "> user services enabled"

DISPLAY=:0 xset s off
DISPLAY=:0 xset s noblank
DISPLAY=:0 xset -dpms
echo "> screen blanking disabled"