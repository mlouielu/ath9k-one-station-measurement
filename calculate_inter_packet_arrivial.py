import sys
from collections import defaultdict
from collections.abc import Iterable
from matplotlib import pyplot as plt
from measure_netlink import codel_time_to_us


def main(filename):
    with open(filename) as f:
        lines = f.readlines()

    timestamps = defaultdict(list)
    wake_timestamps = defaultdict(list)
    for line in lines:
        sta, no, timestamp, mode = line.strip().split('|')

        timestamp = codel_time_to_us(int(timestamp))
        if mode == 'tx':
            timestamps[sta].append(timestamp)
        elif mode == 'wake':
            wake_timestamps[sta].append(timestamp)

    inters = defaultdict(list)
    wake_inters = defaultdict(list)
    for sta in timestamps:
        for i, j in zip(timestamps[sta], timestamps[sta][1:]):
            if j - i > 0:
                inters[sta].append((j - i) / 1000)
        for i, j in zip(wake_timestamps[sta], wake_timestamps[sta][1:]):
            if j - i > 0:
                wake_inters[sta].append((j - i) / 1000)

    fig, axes = plt.subplots(ncols=len(timestamps), sharey=True)
    if not isinstance(axes, Iterable):
        axes = [axes]
    fig.subplots_adjust(wspace=0)
    for ax, data, wake_data, name in zip(axes,
                                         inters.values(),
                                         wake_inters.values(),
                                         inters.keys()):
        ax.boxplot([data, wake_data], labels=['tx', 'wake'])
        ax.set_ylim(0, 20)
        ax.set_xlabel(':'.join(name.split(':')[-2:]))
    plt.show()


if __name__ == '__main__':
    main(sys.argv[1])
