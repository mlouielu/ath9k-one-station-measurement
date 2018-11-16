#!/bin/bash

HOST=192.168.7.222
PORT=5000

curl $HOST:$PORT/bring_trinus_vr_to_top
curl $HOST:$PORT/click_trinus_vr_connect
curl $HOST:$PORT/bring_process_to_top/DiRT

