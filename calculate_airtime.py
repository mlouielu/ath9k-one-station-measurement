import sys
import statistics
from collections import defaultdict


def main(filename):
    dd = defaultdict(lambda: defaultdict(dict))
    usage = defaultdict(lambda: defaultdict(list))
    with open(filename) as f:
        for i in f.readlines():
            sta, counter, timestamp, mode = i.strip().split('|')
            dd[sta][mode][counter] = int(timestamp)

            if mode == 'air':
                try:
                    tx = dd[sta]['tx'][counter]
                    ack = dd[sta]['ack'][counter]
                except KeyError:
                    print(f'[-] Error: {i.strip()}')
                    continue

                diff = ack - tx
                air = int(timestamp)
                usage[sta]['ack'].append(diff)
                usage[sta]['air'].append(air)

    for sta in usage:
        print('=================', sta, '=====================')
        print('Actual time:')
        print(f'mean  : {statistics.mean(usage[sta]["ack"]):.2f}\n'
              f'median: {statistics.median(usage[sta]["ack"])}')
        print('Airtime:')
        print(f'mean  : {statistics.mean(usage[sta]["air"]):.2f}\n'
              f'median: {statistics.median(usage[sta]["air"])}')


if __name__ == '__main__':
    main(sys.argv[1])
