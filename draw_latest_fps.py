#!/bin/python

import sys
import subprocess
import requests


HOST = '192.168.7.222'
PORT = '5000'


if __name__ == '__main__':
    prefix = sys.argv[1]
    j = requests.get(f'http://{HOST}:{PORT}/get_latest_data/{prefix}').json()

    with open(j['filename'], 'w') as f:
        f.write(j['content'])

    subprocess.Popen(['./draw_fps.py', j['filename']]).communicate()
