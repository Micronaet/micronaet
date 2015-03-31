#!/bin/sh
mkdir ~/photo
mkdir ~/photo_dest
sudo mount -t cifs //192.168.100.2/import /home/administrator/photo -o user=administrator,password=password,gid=administrator,uid=administrator
sudo mount -t cifs //192.168.100.2/dest /home/administrator/photo_dest -o user=administrator,password=password,gid=administrator,uid=administrator
