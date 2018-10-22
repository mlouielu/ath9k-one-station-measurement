#!/usr/bin/pypy3
import argparse
import atexit
import re
import socket
import subprocess
import statistics
import math
import os
import select
import matplotlib
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt


# Netlink Settings
NETLINK_NEMS_ATH9K = 31
NETLINK_NEMS_ATH9K_GROUP = 32
NETLINK_BUF_LENGTH = 128
TIMEOUT = 2
sock = None
epoll = None

# IRTT Settings
SECONDS = '15s'
arp_regex = r'(\b(?:\d{1,3}\.){3}\d{1,3}\b)|(\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b)'

# Matplotlib Settings
font = FontProperties()
font.set_family('monospace')
font.set_size('small')
COLOR_PATTLE = {
    '192.168.5.41': 'blue',
    '192.168.5.42': 'green',
    '192.168.5.43': 'red'
}

# Which diff
DIFF_BY_ENQ = True


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
        if mode == 'enq':
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


def get_arp_table():
    arp_table = {}
    output = subprocess.check_output(['arp', '-n']).decode('utf-8')
    for i in output.split('\n'):
        m = re.findall(arp_regex, i)
        if m and len(m) == 2:
            mac = list(filter(lambda x: ':' in x, m[1]))[0]
            ip = list(filter(lambda x: '.' in x, m[0]))[0]
            arp_table[mac] = ip
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
        f'95th:   {diff[math.ceil(95 / 100 * len(diff))]:.3f}ms'
    ]
    return texts


def do_figure(output_path: str, diffs: dict):
    arp_table = get_arp_table()
    figure = plt.figure()
    ax1 = figure.add_subplot(211)
    ax2 = figure.add_subplot(212)
    ax2.axis('off')
    ax1.set_title(f'TX/ACK of 100 bytes UDP packets within 30 seconds\n{output_path}')
    #ax1.set_xscale('log')
    #ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax1.set_xlim((0, 50))
    #ax1.set_xticks([0, 10, 25, 50])

    ip_texts = {}
    for index, host in enumerate(diffs):
        time_diff = diffs[host]
        ip = arp_table[host]
        print(f'host: {ip}, packets: {len(time_diff)}')
        ax1.hist(time_diff, bins='auto', density=True,
                 cumulative=True, label=ip, histtype='step',
                 color=COLOR_PATTLE[ip])
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        texts = '\n'.join(get_result_text(ip, time_diff))
        ip_texts[ip] = texts

    for index, ip in enumerate(sorted(list(ip_texts.keys()))):
        ax2.text(index * 0.3, 0.5, ip_texts[ip], fontsize=10, bbox=props,
                 verticalalignment='center', fontproperties=font)

    legend = ax1.legend(loc='center left', bbox_to_anchor=(1.04, 0.8))
    plt.savefig(f'{output_path}.png',
                bbox_extra_artists=(legend,), bbox_inches='tight')


def do_netlink(subtitle):
    global sock, epoll
    sock = socket.socket(socket.AF_NETLINK,
                         socket.SOCK_RAW, NETLINK_NEMS_ATH9K)
    sock.bind((0, 0))
    sock.setsockopt(270, 1, NETLINK_NEMS_ATH9K_GROUP)
    sock.setblocking(0)
    atexit.register(cleanup_sock)

    epoll = select.epoll()
    epoll.register(sock.fileno(), select.EPOLLIN)
    output = []
    try:
        while True:
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

    diffs = calculate_diffs(output)
    do_figure('enq_' + subtitle, diffs['enq'])
    do_figure('tx_' + subtitle, diffs['tx'])
    do_figure('aggr_' + subtitle, diffs['aggr'])


def run(args):
    # TODO: output file
    subtitle = args[0]
    host = args[1]
    subprocess.Popen(['irtt', 'client', '-i', '10ms', '-l', '100',
                      '-d', SECONDS, '--fill=rand', '--sfill=rand',
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
    parser.add_argument('host', type=str, nargs='+')
    parser.add_argument('--title', type=str)
    parser.add_argument('--time', default=30)
    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.title, args.host)
