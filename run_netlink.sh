#!/bin/bash

IPERF_BITRATE="25M"
IPERF_PARALLEL="4"
IPERF_PROTOCOL="udp"
RUNNING_TIME="22"

if [ "$IPERF_PROTOCOL" == "tcp" ]; then
	IPERF_OPTIONS=""
elif [ "$IPERF_PROTOCOL" == "udp" ]; then
	IPERF_OPTIONS="-u"
fi


TITLE_1="802.11n / 20 MHz / MCS "
TITLE_2=" / 2TP / Bulk $IPERF_BITRATE x $IPERF_PARALLEL - $IPERF_PROTOCOL"


for mcs in 0
do
	sudo sudo iw dev wlp1s0 set bitrates ht-mcs-5 $mcs
	for round in 0
	do
		TITLE="$TITLE_1$mcs$TITLE_2"
		echo $TITLE
		#iperf3 -c 192.168.5.16 -i 1 -t $RUNNING_TIME --fq-rate $IPERF_BITRATE -P $IPERF_PARALLEL -S 0x0 $IPERF_OPTIONS > /dev/null &
		iperf3 -c 192.168.5.42 -i 1 -t $RUNNING_TIME --fq-rate $IPERF_BITRATE -P $IPERF_PARALLEL -S 0x0 $IPERF_OPTIONS > /dev/null &
		iperf3 -c 192.168.5.43 -i 1 -t $RUNNING_TIME --fq-rate $IPERF_BITRATE -P $IPERF_PARALLEL -S 0x0 $IPERF_OPTIONS > /dev/null &
		#iperf3 -c 192.168.5.17 -i 1 -t $RUNNING_TIME --fq-rate $IPERF_BITRATE -P $IPERF_PARALLEL -S 0x0 $IPERF_OPTIONS > /dev/null &
		sudo ./measure_netlink.py --title "$TITLE" --host 192.168.5.41
		pkill iperf3
		sleep 3
	done
done
