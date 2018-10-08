import argparse
import os
import sys
import math
import subprocess
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt


SECONDS = '30s'


def check_if_exist(path, sub):
    counter = 0
    path_t = f'{path}_{counter}{sub}'
    while os.path.exists(path_t):
        counter += 1
        path_t = f'{path}_{counter}{sub}'
    return f'{path}_{counter}'


def main(subtitle, host):
    output_path = subtitle.replace(' ', '').replace('/', '_').strip()
    output_path = check_if_exist('data/' + output_path, '.json.gz')
    output = subprocess.check_output(['irtt', 'client', '-i', '10ms', '-l', '100',
                                      '-d', SECONDS, '--fill=rand', '--sfill=rand',
                                      host, '-o', output_path]).decode('utf-8')
    ends = False
    rtts = []
    rtts_text = []
    for i in output.split('\n'):
        if ends or i.strip().startswith('Min'):
            if i.strip().startswith('RTT'):
                i = i.strip().split()
                rtts_text.append(f'min:    {i[1]}')
                rtts_text.append(f'mean:   {i[2]}')
                rtts_text.append(f'median: {i[3]}')
                rtts_text.append(f'max:    {i[4]}')
                rtts_text.append(f'stddev: {i[5]}')
            ends = True
        elif i.startswith('seq'):
            rtt = i.split()[1].split('=')[-1]
            if rtt.endswith('ms'):
                rtt = float(rtt.strip('ms'))
            elif rtt.endswith('µs'):
                rtt = float(rtt.strip('µs')) / 1000.0
            else:
                raise ValueError(f'Not ms/µs {rtt}')
            rtts.append(rtt)

    rtts.sort()
    rtts_text.append(f'95th:   {rtts[math.ceil(95 / 100 * len(rtts))]}ms')
    print('\n'.join(rtts_text))

    font = FontProperties()
    font.set_family('monospace')
    plt.hist(rtts, len(set(rtts)), density=True, cumulative=True, label='CDF', histtype='step')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.xlim((1, 10))
    plt.text(7, 0.2, '\n'.join(rtts_text), fontsize=10,
             bbox=props, verticalalignment='center', fontproperties=font)
    plt.title(f'RTT of 100 bytes UDP packets within 30 seconds\n{subtitle}')
    plt.savefig(f'{output_path}.jpg')


def get_parser():
    parser = argparse.ArgumentParser(description='Measure RTT')
    parser.add_argument('host', type=str, help='Target host to measure RTT')
    parser.add_argument('--title', type=str, help='Title of the test')
    parser.add_argument('--time', default=30, help='duration of the test')

    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.title, args.host)

