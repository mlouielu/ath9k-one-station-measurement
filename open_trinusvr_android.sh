#!/bin/bash

#adb connect 192.168.5.91:5566
adb shell am force-stop com.loxai.trinus.test
adb shell am start -n com.loxai.trinus.test/com.loxai.trinus.activity.MainActivity
sleep 1
adb shell input tap 0 0
sleep 1
adb shell input tap 320 420
adb shell input tap 638 852 # high performance mode
