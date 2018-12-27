import sys
import statistics
import glob
import json
from collections import defaultdict


def get_iperf_host_and_bandwidth(filename):
    try:
        j = json.load(open(filename))
    except:
        print(filename)
        exit(1)
    return (j['start']['connecting_to']['host'],
            j['end']['sum_sent']['bits_per_second'] / 1024 / 1024)


def calculate_bandwidth_statistics(bandwidths):
    d = {
        'mean': statistics.mean(bandwidths),
        'median': statistics.median(bandwidths),
        'stdev': statistics.stdev(bandwidths),
    }
    return d


def main(files):
    dd = defaultdict(list)
    for f in files:
        try:
            sta, bandwidth = get_iperf_host_and_bandwidth(f)
        except KeyError:
            print('KeyError: ', f)
            exit(1)
        dd[sta].append(bandwidth)

    print('Each station\'s bandwidth')
    all_bandwidth = []
    for sta in dd:
        all_bandwidth.extend(dd[sta])
        print(sta, calculate_bandwidth_statistics(dd[sta]))

    print('All stations bandwidth')
    print(calculate_bandwidth_statistics(all_bandwidth))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory = sys.argv[1:]
        for d in directory:
            files = glob.glob(f'{d.strip("/")}/batch*_iperf*')
            main(files)
    else:
        files = glob.glob('batch*_iperf*')
        main(files)
