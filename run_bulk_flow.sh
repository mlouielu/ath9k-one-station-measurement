#!/bin/bash

RATE=500M
STA1=192.168.5.41
STA2=192.168.5.42
STA3=192.168.5.43

if [ "$1" -eq "0" ];
then
	exit 1
fi

if [ "$1" -ge "1" ];
then
	iperf3 -c $STA1 -i 1 -t 0 --fq-rate $RATE -J --logfile $2_iperf1 &
fi

if [ "$1" -ge "2" ];
then
	iperf3 -c $STA2 -i 1 -t 0 --fq-rate $RATE -J --logfile $2_iperf2 &
fi

if [ "$1" -ge "3" ];
then
	iperf3 -c $STA3 -i 1 -t 0 --fq-rate $RATE -J --logfile $2_iperf3 &
fi
