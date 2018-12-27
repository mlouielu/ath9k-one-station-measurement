#!/bin/bash

RATE=500M
STA0=192.168.5.91
STA1=192.168.5.41
STA2=192.168.5.42
STA3=192.168.5.43
STA4=192.168.5.44

iperf3 -c $STA0 -i 1 -t 0 --fq-rate $RATE -J --logfile $2_iperf0 &

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

if [ "$1" -ge "4" ];
then
	iperf3 -c $STA4 -i 1 -t 0 --fq-rate $RATE -J --locfile $2_iperf4 &
fi

