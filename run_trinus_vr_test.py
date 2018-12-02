#!/bin/python

import argparse
import time
import subprocess
import pexpect
import requests


HOST = '192.168.7.222'
PORT = '5000'


def run(args):
    print('[*] Open Trinus VR on Android')
    subprocess.Popen(['./open_trinusvr_android.sh'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL).communicate()

    print('[*] Windows Trinus VR connect to Android')
    subprocess.Popen(['./start_trinusvr_windows.sh']).communicate()

    # print('[*] Restart the Steam Game (DiRT 3)')
    # subprocess.Popen(['./start_steam_game.sh']).communicate()

    # # Check if the game opened
    # print('    [*] Check if the game is opened')
    # while True:
    #     time.sleep(3)
    #     r = requests.get(f'http://{HOST}:{PORT}/check_process_exist/DiRT')
    #     exist = r.json()['exist']
    #     print(f'    [-] Status: {exist}')
    #     if exist:
    #         break

    print('[*] Bring Game to Top')
    requests.get(f'http://{HOST}:{PORT}/bring_process_to_top/DiRT')
    requests.get(f'http://{HOST}:{PORT}/click/500/500')

    print('[*] Start iperf (if any)')
    iperf = subprocess.Popen(['./run_bulk_flow.sh',
                              str(args.iperf),
                              args.output])

    print('[*] Start Netlink and FPS capture, ready to go')
    netlink = pexpect.spawn(' '.join(['sudo', 'python', './measure_netlink.py',
                             '--netlink', '--subtitle', args.output,
                             '--draw-iperf']))
    requests.get(f'http://{HOST}:{PORT}/get_trinus_vr_fps/{args.pid}/{args.address}/{args.output}')
    time.sleep(args.time + 5)

    print('[*] Done')
    subprocess.Popen(['./open_trinusvr_android.sh']).communicate()
    import os
    subprocess.Popen(['sudo', 'kill', '-2', str(iperf.pid)]).communicate()
    os.system('sudo kill ' + str(iperf.pid))
    os.system('sudo pkill iperf3')
    netlink.sendcontrol('c')
    time.sleep(6)

    # print('[*] Cleanup, closing DiRT')
    # while True:
    #     try:
    #         requests.get(f'http://{HOST}:{PORT}/close_process/dirt3_game')
    #         break
    #     except requests.exceptions.ConnectionError:
    #         print('[-] Cannot close process, retrying...')
    #         subprocess.Popen(['ping', '192.168.7.222', '-c', '1'],
    #                          stdout=subprocess.DEVNULL)
    #         time.sleep(1)

    print('[*] Draw Latest FPS data')
    subprocess.Popen(['./draw_latest_fps.py', args.output]).communicate()


def run_with_all_iperf(args):
    print('[*] Start iperf (if any)')
    iperf = subprocess.Popen(['./run_bulk_flow_and_replace_vr.sh',
                              str(args.iperf),
                              args.output])
    print('[*] Start Netlink capture, ready to go')
    netlink = pexpect.spawn(' '.join(['sudo', 'python', './measure_netlink.py',
                             '--netlink', '--subtitle', args.output,
                             '--draw-iperf']))
    time.sleep(args.time + 3)

    print('[*] Done')
    import os
    subprocess.Popen(['sudo', 'kill', '-2', str(iperf.pid)]).communicate()
    #os.system('sudo kill ' + str(iperf.pid))
    #os.system('sudo pkill iperf3')
    netlink.sendcontrol('c')
    time.sleep(5)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int)
    parser.add_argument('--address', type=str)
    parser.add_argument('--output', type=str)
    parser.add_argument('--time', type=int)
    parser.add_argument('--iperf', type=int)
    parser.add_argument('--replace-vr', action='store_true', default=False)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()

    if args.replace_vr:
        run_with_all_iperf(args)
    else:
        run(args)
