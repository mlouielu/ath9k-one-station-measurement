#!/usr/bin/pypy3

import socket
import select
import time
import numpy as np
from measure_netlink import codel_time_to_us


NETLINK_NEMS_ATH9K = 31
NETLINK_NEMS_ATH9K_GROUP = 32
NETLINK_BUF_LENGTH = 64
TIMEOUT = 20
sock = None
epoll = None

TARGET_MAC_ADDR = 'd4:6e:0e:65:aa:74'
#TARGET_MAC_ADDR = '24:18:1d:71:71:c8'


def get_airtime_quantum_low():
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_low') as f:
        return int(f.read())


def set_airtime_quantum_low(quantum):
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_low', 'w') as f:
        f.write(str(quantum))


def get_airtime_quantum_high():
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_high') as f:
        return int(f.read())


def set_airtime_quantum_high(quantum):
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_high', 'w') as f:
        f.write(str(quantum))


def main():
    global sock, epoll
    sock = socket.socket(socket.AF_NETLINK,
                         socket.SOCK_RAW, NETLINK_NEMS_ATH9K)
    sock.bind((0, 0))
    sock.setsockopt(270, 1, NETLINK_NEMS_ATH9K_GROUP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 28)
    sock.setblocking(0)

    epoll = select.epoll()
    epoll.register(sock.fileno(), select.EPOLLIN)

    previous = None
    time_diff = []
    count = 0
    previous_changed_timestamp = None
    try:
        while True:
            events = epoll.poll(timeout=TIMEOUT)
            if not events:
                break
            for fileno, event in events:
                if event & select.EPOLLIN:
                    b = sock.recvfrom(NETLINK_BUF_LENGTH)[0]
                    b = b[b.find(b'[') + 1: b.find(b']')].decode('utf-8')
                    addr, seqno, timestamp, mode = b.split('|')

                    if addr != TARGET_MAC_ADDR:
                        continue

                    if mode != 'tx':
                        continue

                    timestamp = codel_time_to_us(int(timestamp)) / 1000
                    if not previous:
                        previous = timestamp
                        continue
                    else:
                        diff = timestamp - previous

                        # TX timeout
                        if diff > 5000.0:
                            previous = None
                            time_diff = []
                            count = 0
                            set_airtime_quantum_high(300)
                            continue

                        time_diff.append(timestamp - previous)
                        count += 1
                        previous = timestamp

                    if count == 300:
                        p_95 = np.percentile(time_diff, 95)
                        print(f'{get_airtime_quantum_high():04d} {p_95:.3f}')

                        time_diff.pop(0)
                        count -= 1

                        set_aqh = 0
                        aqh = get_airtime_quantum_high()
                        if p_95 > 8:
                            if not previous_changed_timestamp:
                                previous_changed_timestamp = time.time()
                                continue
                            if not (time.time() - previous_changed_timestamp > 1):
                                continue
                            if aqh > 2000:
                                continue
                            set_aqh = aqh + 50
                        elif p_95 < 6:
                            if aqh - 100 >= 100:
                                set_aqh = aqh - 100

                        if set_aqh:
                            set_airtime_quantum_high(set_aqh)
                            previous_changed_timestamp = time.time()
    except socket.timeout:
        sock.close()


if __name__ == '__main__':
    main()
