import argparse
import os
import math
import subprocess
import matplotlib
from concurrent.futures import ProcessPoolExecutor
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt


SECONDS = '30s'
font = FontProperties()
font.set_family('monospace')
font.set_size('small')


def check_if_exist(path, sub):
    counter = 0
    path_t = f'{path}_{counter}{sub}'
    while os.path.exists(path_t):
        counter += 1
        path_t = f'{path}_{counter}{sub}'
    return f'{path}_{counter}'


def run(args):
    subtitle = args[0]
    host = args[1]
    output_path = subtitle.replace(' ', '').replace('/', '_').strip()
    output_path = check_if_exist('data/' + output_path, '.json.gz')
    output = subprocess.check_output(['irtt', 'client', '-i', '10ms', '-l', '100',
                                      '-d', SECONDS, '--fill=rand', '--sfill=rand',
                                      host, '-o', output_path]).decode('utf-8')
    ends = False
    rtts = []
    rtts_text = [f'host: {host}']
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
    return (rtts, rtts_text)


def main(subtitle, hosts):
    output_path = subtitle.replace(' ', '').replace('/', '_').strip()
    output_path = check_if_exist(output_path, '.jpg')

    figure = plt.figure()
    ax1 = figure.add_subplot(211)
    ax2 = figure.add_subplot(212)
    ax1.set_title(f'RTT of 100 bytes UDP packets within 30 seconds\n{subtitle}')
    ax2.axis('off')
    ax1.set_xscale('log')
    ax1.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax1.set_xlim((1, 500))
    ax1.set_xticks([1, 10, 100, 250, 500])

    max_rtt = 0
    with ProcessPoolExecutor(max_workers=len(hosts)) as executor:
        for index, (host, result) in enumerate(zip(hosts, executor.map(run, ((subtitle, host) for host in hosts)))):
            print(host, result[1])
            ax1.hist(result[0], len(set(result[0])), density=True, cumulative=True,
                     label=host, histtype='step')
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            max_rtt = max(max_rtt, max(result[0]))
            ax2.text(index * 0.3, 0.5, '\n'.join(result[1]), fontsize=10,
                     bbox=props, verticalalignment='center', fontproperties=font)

        legend = ax1.legend(loc="center left", bbox_to_anchor=(1.04, 0.8))
        plt.savefig(f'{output_path}.jpg', bbox_extra_artists=(legend,), bbox_inches='tight')


def get_parser():
    parser = argparse.ArgumentParser(description='Measure RTT')
    parser.add_argument('host', type=str, nargs='+', help='Target host to measure RTT')
    parser.add_argument('--title', type=str, help='Title of the test')
    parser.add_argument('--time', default=30, help='duration of the test')

    return parser


if __name__ == '__main__':
    args = get_parser().parse_args()
    main(args.title, args.host)

