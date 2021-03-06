#!/bin/bash

for mcs in 0 1 2 4 7 8 9 10 12 15
do
	sudo sudo iw dev wlp1s0 set bitrates ht-mcs-5 $mcs
	for round in 0 1 2
	do
		echo "802.11n / 20 MHz / MCS $mcs / 3TP / Bulk4M"
		python measure.py --title "802.11n / 20 MHz / MCS $mcs / 3TP / Bulk4M" 192.168.5.41 192.168.5.42 192.168.5.43
	done
done
