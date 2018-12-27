#!/bin/bash

ssh root@192.168.5.41 "/etc/init.d/iperf3 restart"
ssh root@192.168.5.42 "/etc/init.d/iperf3 restart"
ssh root@192.168.5.43 "/etc/init.d/iperf3 restart"

