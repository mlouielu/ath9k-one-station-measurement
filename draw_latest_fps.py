#!/bin/python

import sys
import time
import json
import subprocess
import requests


HOST = '192.168.7.222'
PORT = '5000'


if __name__ == '__main__':
    retry = 0
    prefix = sys.argv[1]
    while retry < 10:
        try:
            r = requests.get(f'http://{HOST}:{PORT}/get_latest_data/{prefix}')
            j = r.json()
            break
        except requests.exceptions.ConnectionError:
            print(f'[-] Cannot get latest data of {prefix}, retrying...')
            retry += 1
            time.sleep(1)
        except json.decoder.JSONDecodeError:
            print(f'[-] JSON decode error: {r.content}, retrying...')
            retry += 1
            time.sleep(1)

    if retry == 10:
        print('[-] Retry to much time, failed...')
        exit(1)

    with open(j['filename'], 'w') as f:
        f.write(j['content'])

    subprocess.Popen(['./draw_fps.py', j['filename']]).communicate()
