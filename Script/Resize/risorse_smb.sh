#!/bin/bash
# Parameter to change:
user="administrator@domain.local"
password="pwd"
gid="administrator"
uid="administrator"
server="pc03"
share="per nicola"
mount_point="/home/administrator/Images/ETL/Resize"

sudo umount $mount_point
sudo mount -t cifs "//$server/$share $mount_point" -o user=$user,password=$password,gid=$gid,uid=$uid

