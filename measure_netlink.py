#!/usr/bin/pypy3
import atexit
import socket
import statistics

NETLINK_NEMS_ATH9K = 31
NETLINK_NEMS_ATH9K_GROUP = 32
NETLINK_BUF_LENGTH = 128


def cleanup_sock():
    sock.close()


def print_time_diff_stats(diffs):
    if len(diffs) < 2:
        return
    print('Min\tMean\tMedian\tMax\tStddev')
    print('{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}'.format(
        min(diffs), statistics.mean(diffs), statistics.median(diffs),
        max(diffs), statistics.stdev(diffs)))


sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, NETLINK_NEMS_ATH9K)
sock.bind((0, 0))
sock.setsockopt(270, 1, NETLINK_NEMS_ATH9K_GROUP)
atexit.register(cleanup_sock)


ack_timestamps = {}
tx_timestamps = {}
time_diffs = []
while True:
    b = sock.recvfrom(NETLINK_BUF_LENGTH)[0]
    b = b[b.find(b'[') + 1: b.find(b']')].decode('utf-8')
    addr, seqno, timestamp, mode = b.split('|')
    if not addr.startswith('d4:6e:0e:65:aa:74'):
        continue
    if mode == 'tx':
        tx_timestamps[seqno] = int(timestamp)
    elif mode == 'ack':
        ack_timestamps[seqno] = int(timestamp)
        if seqno in tx_timestamps:
            time_diff = (ack_timestamps[seqno] - tx_timestamps[seqno]) / 1000
            time_diffs.append(time_diff)
            #print(f'mac: {addr}, seqno: {seqno}, diff: {time_diff}')
        else:
            print('Why I do not have this seqno: {}'.format(seqno))
    print_time_diff_stats(time_diffs)
