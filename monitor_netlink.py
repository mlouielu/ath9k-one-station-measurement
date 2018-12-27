#!/usr/bin/pypy3

import socket
import select


NETLINK_NEMS_ATH9K = 31
NETLINK_NEMS_ATH9K_GROUP = 32
NETLINK_BUF_LENGTH = 64
TIMEOUT = 20
sock = None
epoll = None

TARGET_MAC_ADDR = 'd4:6e:0e:65:aa:74'


def get_airtime_quantum_low():
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_low') as f:
        return int(f.read())


def set_airtime_quantum_low(quantum):
    with open('/sys/kernel/debug/ieee80211/phy0/ath9k/airtime_quantum_low', 'w') as f:
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

    enq_timestamp = {}
    air_timestamp = {}
    ack_timestamp = {}
    latency = []
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

                    #if addr != TARGET_MAC_ADDR:
                    #    continue

                    print(b)
                    continue

                    if mode == 'enq':
                        enq_timestamp[seqno] = int(timestamp)
                    elif mode == 'ack':
                        ack_timestamp[seqno] = int(timestamp)
                        if seqno in enq_timestamp:
                            latency.append((int(timestamp) - enq_timestamp[seqno]) / 1000)
                            # enq_timestamp.pop(seqno)
                    elif mode == 'air':
                        if seqno in ack_timestamp and seqno in enq_timestamp:
                            print(int(timestamp),
                                  ack_timestamp[seqno] - enq_timestamp[seqno])

                    if len(latency) > 200:
                        latency.pop(0)

                    if len(latency) == 200:
                        a = sum(latency[:100]) / 100
                        b = sum(latency) / 200
                        current_quantum = get_airtime_quantum_low()
                        #print(f'{a: 5.3f} {b: 5.3f}', get_airtime_quantum_low())
                        if a > 15:
                            set_airtime_quantum_low(max(50, current_quantum - 5))
                        else:
                            set_airtime_quantum_low(min(500, current_quantum + 2))
    except socket.timeout:
        sock.close()


if __name__ == '__main__':
    main()
