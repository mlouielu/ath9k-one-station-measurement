#!/bin/bash

for mcs in 0 1 2 4 8
do
	sudo sudo iw dev wlp1s0 set bitrates ht-mcs-5 $mcs
	for round in 0 1 2
	do
		echo "802.11n / 20 MHz / MCS $mcs"
		python measure.py "802.11n / 20 MHz / MCS $mcs"
	done
done
