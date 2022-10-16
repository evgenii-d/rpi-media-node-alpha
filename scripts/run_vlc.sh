#!/bin/bash
app_folder=$(dirname $(dirname $(realpath $0)))
script_folder=$(dirname $(realpath $0))
playlist="$app_folder/static/media/playlist.m3u"
audio_config=~/.asoundrc
vlc_config=~/.config/vlc/vlcrc
headphones=$(grep "\[Headphones" /proc/asound/cards | cut -c -2 | tr -d '\r' | tr -d '\n')
rc_host=$(grep "\bhost\b" $app_folder/config.ini | cut -c 8- | tr -d '\r')
rc_port=$(grep "\bport\b" $app_folder/config.ini | cut -c 8- | tr -d '\r')
module=$(grep "\bmodule\b" $app_folder/config.ini | cut -c 10- | tr -d '\r')
options=$(grep "\boptions\b" $app_folder/config.ini | cut -c 11- | tr -d '\r')
settings="-f -I dummy --video-on-top --no-video-title-show --playlist-autostart --extraintf oldrc --rc-fake-tty --rc-host=$rc_host:$rc_port"

# check audio config file
if ! test -f $audio_config; then
    cp $script_folder/.asoundrc ~/
fi

# set audio output
sed -i "s/card.*/card $headphones/" $audio_config

# check vlc config file
if ! test -f $vlc_config; then
    cp $script_folder/vlcrc ~/.config/vlc/
fi

# set video output module
sed -i "s/^#vout=.*/vout=$module/" $vlc_config
sed -i "s/^vout=.*/vout=$module/" $vlc_config
echo "Video output module: $module"

vlc $playlist $settings $options