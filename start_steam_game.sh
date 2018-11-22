#!/bin/bash

HOST=192.168.7.222
PORT=5000

curl $HOST:$PORT/close_process/dirt3_game
curl $HOST:$PORT/open_steam_game
