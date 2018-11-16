#!/bin/bash

adb shell am force-stop com.loxai.trinus.test
adb shell am start -n com.loxai.trinus.test/com.loxai.trinus.activity.MainActivity
adb shell input tap 0 0
adb shell input tap 320 420
