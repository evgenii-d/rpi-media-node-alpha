# RPi Media Node

Image for *Raspberry Pi 4* based on Debian 10 (buster), which allows using Raspberry Pi in kiosk mode to play video and audio files.

# Usage
1. Go to [releases section](https://github.com/evgenii-d/rpi-media-node/releases)
2. Download the `.7z` file
3. Extract image and flash SD using [etcher](https://www.balena.io/etcher/) or similar software
4. Raspberry Pi must be connected to the network via cable

After that, Raspberry Pi can be found on the network either by IP address (DHCP) or via mdns (zeroconf). Web app port - 5000
<br>
Something like this:
* IP - http://192.168.1.201:5000/
* zeroconf - http://node-1f33c68f.local:5000/
<br>

# Features
* By default you can upload `.mp4`, `.webm`, `.mkv`, `.mp3` and `.wav` files.
* Videos encoded with *H.265* codec are *preferred*. In this case Raspberry Pi 4 can handle videos in 4k (3840x2160) 60fps.
* If you want to use both micro HDMI ports (mirror mode), then 
  * encode videos with *H.264* (only FullHD video supported)
  * check `gles2` in *Additional settings* section
  * reboot node or press `Quit` button in *Player control* section
* Audio output is available via 3.5mm jack

# Overview
![web app](https://github.com/evgenii-d/rpi-media-node/blob/main/media-node-contol.png)
