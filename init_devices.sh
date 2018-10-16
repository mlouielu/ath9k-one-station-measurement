#!/bin/bash

declare -a hosts=("192.168.5.41" "192.168.5.42" "192.168.5.43")

for host in "${hosts[@]}"
do
	ssh root@$host "iw phy phy0 set rts off"
	ssh root@$host "iw phy phy1 set rts off"
	ssh root@$host "iw dev wlan0 set power_save off"
done
