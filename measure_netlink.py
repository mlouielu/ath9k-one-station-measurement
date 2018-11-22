#!/usr/bin/pypy3
import argparse
import atexit
import glob
import json
import re
import socket
import subprocess
import statistics
import math
import os
import select
import signal

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt


# Netlink Settings
NETLINK_NEMS_ATH9K = 31
NETLINK_NEMS_ATH9K_GROUP = 32
NETLINK_BUF_LENGTH = 64
TIMEOUT = 2
sock = None
epoll = None

# IRTT Settings
SECONDS = '20s'
DSCP = '0x0'
arp_regex = r'(\b(?:\d{1,3}\.){3}\d{1,3}\b)|(\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b)'

# Matplotlib Settings
font = FontProperties()
font.set_family('monospace')
font.set_size('small')
COLOR_PATTLE = {
    '192.168.5.91': 'm',
    '192.168.5.41': 'blue',
    '192.168.5.42': 'green',
    '192.168.5.43': 'red',
    '192.168.5.16': 'orange',
    '192.168.5.17': 'purple'
}

# Which diff
DIFF_BY_ENQ = True

# Netlink Loop Enable
NETLINK_LOOP = False


def ctrl_c_signal_handler(signum, frame):
    global NETLINK_LOOP
    if NETLINK_LOOP:
        NETLINK_LOOP = False
    else:
        exit(0)


def cleanup_sock():
    epoll.unregister(sock.fileno())
    epoll.close()
    sock.close()


def check_if_exist(path, sub, prefix=None):
    counter = 0
    if prefix:
        path_t = f'{prefix}{path}_{counter}{sub}'
    else:
        path_t = f'{path}_{counter}{sub}'
    while os.path.exists(path_t):
        counter += 1
        if prefix:
            path_t = f'{prefix}{path}_{counter}{sub}'
        else:
            path_t = f'{path}_{counter}{sub}'
    return f'{path}_{counter}'


def calculate_diffs(output: list):
    enq_timestamps = defaultdict(dict)
    tx_timestamps = defaultdict(dict)
    ack_timestamps = defaultdict(dict)
    wake_timestamps = defaultdict(dict)
    aggr_timestamps = defaultdict(dict)
    diff_timestamps = defaultdict(lambda: defaultdict(list))

    for i in output:
        addr, seqno, timestamp, mode = i.split('|')
        if mode == 'hit1':
            round = int(seqno)
            now = int(timestamp)
            diff_timestamps['now'][addr].append(now / 1000)
        elif mode == 'hit2':
            left = int(seqno)
            slot_left = int(timestamp)
        elif mode == 'enq':
            enq_timestamps[addr][seqno] = int(timestamp)
        elif mode == 'wake':
            wake_timestamps[addr][seqno] = int(timestamp)
        elif mode == 'aggr':
            aggr_timestamps[addr][seqno] = int(timestamp)
            if seqno in wake_timestamps[addr]:
                diff_timestamps['aggr'][addr].append(
                    (aggr_timestamps[addr][seqno] - wake_timestamps[addr][seqno]) / 1000)
        elif mode == 'tx':
            tx_timestamps[addr][seqno] = int(timestamp)
        elif mode == 'ack':
            ack_timestamps[addr][seqno] = int(timestamp)
            if seqno in enq_timestamps[addr]:
                diff_timestamps['enq'][addr].append(
                   (ack_timestamps[addr][seqno] - enq_timestamps[addr][seqno]) / 1000)
            if seqno in tx_timestamps[addr]:
                diff_timestamps['tx'][addr].append(
                    (ack_timestamps[addr][seqno] - tx_timestamps[addr][seqno]) / 1000)
    return diff_timestamps


def ping_them():
    subprocess.Popen(['ping', '192.168.5.91', '-c', '1'], stdout=subprocess.DEVNULL)
    subprocess.Popen(['ping', '192.168.5.42', '-c', '1'], stdout=subprocess.DEVNULL)
    subprocess.Popen(['ping', '192.168.5.43', '-c', '1'],
                     stdout=subprocess.DEVNULL).communicate()


def get_arp_table():
    arp_table = {}
    ping_them()
    output = subprocess.check_output(['arp', '-n']).decode('utf-8')
    for i in output.split('\n'):
        m = re.findall(arp_regex, i)
        if m and len(m) == 2:
            mac = list(filter(lambda x: ':' in x, m[1]))[0]
            ip = list(filter(lambda x: '.' in x, m[0]))[0]
            arp_table[mac] = ip

    # Hardcode ARP
    arp_table['24:18:1d:71:71:c8'] = '192.168.5.91'
    return arp_table


def get_result_text(ip, diff):
    diff.sort()
    texts = [
        f'host: {ip}',
        f'packets:{len(diff)}',
        f'min:    {min(diff):.3f}',
        f'mean:   {statistics.mean(diff):.3f}',
        f'median: {statistics.median(diff):.3f}',
        f'max:    {max(diff):.3f}',
        f'stddev: {statistics.stdev(diff):.3f}',
        f'80th:   {diff[math.ceil(80 / 100 * len(diff))]:.3f}ms',
        f'90th:   {diff[math.ceil(90 / 100 * len(diff))]:.3f}ms',
        f'95th:   {diff[math.ceil(95 / 100 * len(diff))]:.3f}ms'
    ]
    return texts


def get_iperf_result_from_files(prefix):
    d = {}
    for filename in glob.glob(f'{prefix}_iperf*'):
        j = json.load(open(filename))
        dst = j['start']['connecting_to']['host']
        mbits_per_second = j['end']['sum_sent']['bits_per_second'] / 1024 / 1024
        d[dst] = mbits_per_second

    return d


def do_figure(output_path: str, diffs: dict, cumulative=True, iperf_prefix=None):
    arp_table = get_arp_table()
    figure = plt.figure()
    ax1 = figure.add_subplot(211)
    ax2 = figure.add_subplot(212)
    ax2.axis('off')
    ax1.set_title(f'TX/ACK of 100 bytes UDP packets within {SECONDS.strip("s")} seconds\n{output_path}')
    #ax1.set_xscale('log')
    #ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    if output_path.startswith('aggr'):
        ax1.set_xlim((0, 10))
    else:
        ax1.set_xlim((0, 50))
    #ax1.set_xticks([0, 10, 25, 50])

    iperf_result = None if not iperf_prefix else get_iperf_result_from_files(iperf_prefix)
    ip_texts = {}
    for index, host in enumerate(diffs):
        if len(diffs[host]) < 10:
            continue
        time_diff = diffs[host]
        try:
            ip = arp_table[host]
        except KeyError:
            print(f'{host} not in arp table...')
            continue
        print(f'host: {ip}, packets: {len(time_diff)}')
        ax1.hist(time_diff, bins='auto', density=True,
                 cumulative=cumulative, label=ip, histtype='step',
                 color=COLOR_PATTLE[ip])
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        texts = '\n'.join(get_result_text(ip, time_diff))
        if iperf_result and ip in iperf_result:
            texts += f'\niperf:  {iperf_result[ip]:.3f}Mb/s'
        ip_texts[ip] = texts

    for index, ip in enumerate(sorted(list(ip_texts.keys()))):
        ax2.text(index * 0.3, 0.5, ip_texts[ip], fontsize=10, bbox=props,
                 verticalalignment='center', fontproperties=font)

    legend = ax1.legend(loc='center left', bbox_to_anchor=(1.04, 0.8))
    plt.savefig(f'{output_path}.png',
                bbox_extra_artists=(legend,), bbox_inches='tight')


def save_output(path, raw_output):
    with open(path, 'w') as f:
        for i in raw_output:
            f.write(f'{i}\n')


def do_netlink(subtitle, iperf=False):
    global sock, epoll, NETLINK_LOOP
    sock = socket.socket(socket.AF_NETLINK,
                         socket.SOCK_RAW, NETLINK_NEMS_ATH9K)
    sock.bind((0, 0))
    sock.setsockopt(270, 1, NETLINK_NEMS_ATH9K_GROUP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 28)
    sock.setblocking(0)
    atexit.register(cleanup_sock)

    epoll = select.epoll()
    epoll.register(sock.fileno(), select.EPOLLIN)
    output = []

    NETLINK_LOOP = True
    signal.signal(signal.SIGINT, ctrl_c_signal_handler)
    try:
        while NETLINK_LOOP:
            events = epoll.poll(timeout=TIMEOUT)
            if not events:
                break
            for fileno, event in events:
                if event & select.EPOLLIN:
                    b = sock.recvfrom(NETLINK_BUF_LENGTH)[0]
                    b = b[b.find(b'[') + 1: b.find(b']')].decode('utf-8')
                    output.append(b)
    except socket.timeout:
        sock.close()

    if iperf:
        # Kill iperf so make sure we have logfile
        subprocess.Popen(['sudo', 'pkill', '-2', 'iperf3']).communicate()

    diffs = calculate_diffs(output)
    do_figure('enq_' + subtitle, diffs['enq'],
              iperf_prefix=subtitle if iperf else None)
    #do_figure('tx_' + subtitle, diffs['tx'])
    #do_figure('aggr_' + subtitle, diffs['aggr'])
    #do_figure('now_' + subtitle, diffs['now'])
    save_output('output_' + subtitle, output)


def draw_figure_from_input(inputs, output_path):
    arp_table = get_arp_table()
    figure = plt.figure(figsize=(10, 10))
    ax1 = figure.add_subplot(211)
    ax2 = figure.add_subplot(212)
    ax2.axis('off')
    ax1.set_title(f'')
    ax1.set_xlim((0, 50))

    output_texts = {}
    for i in inputs:
        with open(i) as f:
            print(i)
            diffs = calculate_diffs(f.read().strip().split('\n'))['enq']
        host = '24:18:1d:71:71:c8'
        time_diff = diffs[host]
        ip = arp_table[host]
        ax1.hist(time_diff, bins='auto', density=True,
                 cumulative=True, label=i, histtype='step')

        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        texts = '\n'.join([i] + get_result_text(ip, time_diff))
        #texts = '\n'.join([i[i.find('MCS'):i.find('_Bulk')] + f'_{len(i)}'] + get_result_text(ip, time_diff))
        output_texts[i] = texts

    for index, i in enumerate(sorted(list(output_texts.keys()))):
        ax2.text((index % 6) * 0.2, 0.8 if index < 6 else 0.3, output_texts[i], fontsize=10, bbox=props,
                 verticalalignment='center', fontproperties=font)

    legend = ax1.legend(loc='center left', bbox_to_anchor=(1.04, 0.8))
    plt.savefig(f'{output_path}.png',
                bbox_extra_artists=(legend,), bbox_inches='tight')


def run(args):
    # TODO: output file
    subtitle = args[0]
    host = args[1]
    subprocess.Popen(['irtt', 'client', '-i', '10ms', '-l', '100',
                      '-d', SECONDS, '--fill=rand', '--sfill=rand', f'--dscp={DSCP}',
                      host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(subtitle, hosts):
    output_path = subtitle.replace(' ', '').replace('/', '_').strip()
    output_path = check_if_exist(output_path, '.png', prefix='tx_')
    with ProcessPoolExecutor(max_workers=len(hosts)) as executor:
        for host in hosts:
            executor.submit(run, (subtitle, host))
    do_netlink(output_path)


def get_parser():
    parser = argparse.ArgumentParser(description='Measure tx/ack via netlink')
    parser.add_argument('--host', type=str, nargs='+')
    parser.add_argument('--subtitle', type=str)
    parser.add_argument('--time', default=30)

    parser.add_argument('--input', type=str, nargs='+')
    parser.add_argument('--output', type=str)

    parser.add_argument('--netlink', default=False, action='store_true')
    parser.add_argument('--draw-iperf', default=False, action='store_true')
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()

    if args.input:
        draw_figure_from_input(args.input, args.output)
    elif args.netlink and args.subtitle:
        do_netlink(args.subtitle, args.draw_iperf)
    else:
        main(args.subtitle, args.host)
