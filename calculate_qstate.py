import sys
from collections import defaultdict


def main(filename):
    with open(filename) as f:
        lines = f.readlines()

    qstates = defaultdict(lambda: defaultdict(int))
    for line in lines:
        sta, q, timestamp, mode = line.strip().split('|')
        if mode != 'qstate':
            continue

        qstates[sta][int(q)] += 1

    for sta in qstates:
        print(sta, dict(qstates[sta]))


if __name__ == '__main__':
    main(sys.argv[1])
