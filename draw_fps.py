#!/bin/python

import os
import sys
import matplotlib.pyplot as plt


def get_data(filename):
    data = []
    with open(filename) as f:
        lines = f.read().strip('\n').split('\n')
        for i in lines:
            time, fps, bandwidth = i.split()
            data.append([float(time), int(fps.split('/')[1]), float(bandwidth)])
    return data


def draw(filename):
    fig, ax1 = plt.subplots()
    data = get_data(filename)

    # timestamps = [i[0] for i in data]
    # Minus 3 because use three 0 bandwidth as stop sending
    timestamps = range(len(data) - 3)
    fps = [i[1] for i in data[:-3]]
    bandwidth = [i[2] for i in data[:-3]]

    ax1.plot(timestamps, fps, 'r')
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('fps')
    ax1.set_ylim(0, 80)

    ax2 = ax1.twinx()
    ax2.plot(timestamps, bandwidth, 'b--')
    ax2.set_ylabel('Bandwidth (Mbit/s)')
    ax2.set_ylim(0, 100)

    fig.tight_layout()
    plt.savefig(f'{os.path.splitext(filename)[0]}.png')


if __name__ == '__main__':
    for i in sys.argv[1:]:
        draw(i)
