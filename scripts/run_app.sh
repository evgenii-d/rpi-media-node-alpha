#!/bin/bash
app_folder=$(dirname $(dirname $(realpath $0)))
script_folder=$(dirname $(realpath $0))
hostname=$script_folder/hostname

# generate new hostname if there is now file "hostname"
if ! test -f $hostname; then
    random_string=$(shuf -er -n8 {a..z} {0..9} | tr -d '\n')
    touch $hostname
    sudo hostnamectl set-hostname "node-$random_string"
    sudo shutdown -r now
fi

echo "Start media node web app"
$app_folder/venv/bin/python $app_folder/main.py
