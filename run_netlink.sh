#!/bin/bash

IPERF_BITRATE="60M"
IPERF_PARALLEL="5"
IPERF_PROTOCOL="tcp"

if [ "$IPERF_PROTOCOL" == "tcp" ]; then
	IPERF_OPTIONS=""
elif [ "$IPERF_PROTOCOL" == "udp"]; then
	IPERF_OPTIONS="-u"
fi


TITLE_1="802.11n / 40 MHz / MCS "
TITLE_2=" / 3TP / Bulk $IPERF_BITRATE x $IPERF_PARALLEL - $IPERF_PROTOCOL"


for mcs in 0 1 2 4 7 8 9 10 12 15
do
	sudo sudo iw dev wlp1s0 set bitrates ht-mcs-5 $mcs
	for round in 0 1 2
	do
		TITLE="$TITLE_1$mcs$TITLE_2"
		echo $TITLE
		iperf3 -c 192.168.5.16 -i 1 -t 0 -b $IPERF_BITRATE -P $IPERF_PARALLEL -S 0x0 $IPERF_OPTIONS > /dev/null &
		sudo ./measure_netlink.py --title "$TITLE" 192.168.5.41 192.168.5.42 192.168.5.43
		pkill iperf3
	done
done
