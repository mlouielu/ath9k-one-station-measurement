#!/bin/python

import argparse
import time
import subprocess


HOST = '192.168.7.222'


def run(args):
    subprocess.Popen(['./open_trinusvr_android.sh']).communicate()
    subprocess.Popen(['./start_trinusvr_windows.sh']).communicate()
    subprocess.Popen(['ssh', f'louie@{HOST}',
                      f'"python get_trinus_vr_fps.py --pid {args.pid} --address {args.address}'
                      f' --output {args.output}"'])
    time.sleep(args.time)
    subprocess.Popen(['./open_trinusvr_android.sh']).communicate()
    time.sleep(5)

    subprocess.Popen(['./draw_latest_fps.py', args.output]).communicate()


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int)
    parser.add_argument('--address', type=str)
    parser.add_argument('--output', type=str)
    parser.add_argument('--time', type=int)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()

    run(args)
