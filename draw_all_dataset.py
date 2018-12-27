import concurrent.futures
import math
import statistics
import sys
import glob
from collections import defaultdict
from matplotlib import pyplot as plt

import calculate_fps
import calculate_bulk_bandwidth
import measure_netlink


TARGET_MAC = '24:18:1d:71:71:c8'
airtime_datasets = defaultdict(lambda: defaultdict(list))
resp_datasets = defaultdict(lambda: defaultdict(list))


def get_human_readable_names(original_names):
    names = []
    for n in original_names:
        i = n.split('_')
        s = ''
        s += ':'.join(i[:2]) + '\n'
        s += i[2] + '\n'
        s += ':'.join(i[3:5]) + '\n'
        s += ':'.join(i[5:7]) + '\n'
        s += f'low :{i[8]}\n'
        s += f'high:{i[9]}\n'
        s += f'rept:{i[-1]}\n'
        names.append(s)
    return names


def read_fps_bandwidth(filename, d):
    global airtime_datasets, resp_datasets
    with open(filename) as f:
        data = f.readlines()
        try:
            fps, bandwidth = calculate_fps.get_data(data)
        except ValueError:
            print(f'[-] VR fps data error: {filename}')
            return

        if 'resp' in d:
            resp_datasets['fps'][d].extend(fps)
            resp_datasets['bandwidth'][d].extend(bandwidth)
            try:
                resp_datasets['overall_bandwidth_vr'][d].append(
                    statistics.mean(bandwidth))
            except statistics.StatisticsError:
                pass
        else:
            airtime_datasets['fps'][d].extend(fps)
            airtime_datasets['bandwidth'][d].extend(bandwidth)
            try:
                airtime_datasets['overall_bandwidth_vr'][d].append(
                    statistics.mean(bandwidth))
            except statistics.StatisticsError:
                pass


def read_vr_latency(filename, d):
    global airtime_datasets, resp_datasets
    with open(filename) as f:
        diffs = measure_netlink.calculate_diffs(f.read().strip().split('\n'))
        enq_diffs = diffs['enq'][TARGET_MAC]
        if list(filter(lambda x: x < 0, enq_diffs)):
            print(f'[*] latency data not correct: {filename}, skip...')
            return

        if 'resp' in d:
            resp_datasets['latency'][d].extend(enq_diffs)
        else:
            airtime_datasets['latency'][d].extend(enq_diffs)


def read_bulk_bandwidth(filename, d):
    global airtime_datasets, resp_datasets
    try:
        sta, bandwidth = calculate_bulk_bandwidth.get_iperf_host_and_bandwidth(filename)
    except KeyError:
        return
    if 'resp' in d:
        resp_datasets['bulk'][d].append(bandwidth)
    else:
        airtime_datasets['bulk'][d].append(bandwidth)


def read_data(d):
    global airtime_datasets, resp_datasets
    print(d)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # VR FPS, Bandwidth
        filenames = glob.glob(f'{d.strip("/")}/*.txt')
        for filename in filenames:
            results.append(executor.submit(read_fps_bandwidth, filename, d))

        # VR latency
        filenames = glob.glob(f'{d.strip("/")}/output_*')
        for filename in filenames:
            results.append(executor.submit(read_vr_latency, filename, d))

        # Bulk latency
        filenames = glob.glob(f'{d.strip("/")}/batch*_iperf*')
        for filename in filenames:
            results.append(executor.submit(read_bulk_bandwidth, filename, d))

        for r in results:
            r.result()


def main(directories):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = []
        for d in directories:
            results.append(executor.submit(read_data, d))
        for r in results:
            r.result()

    anames = sorted(airtime_datasets['fps'].keys())
    rnames = sorted(resp_datasets['fps'].keys())

    # Calculate overall bandwidth
    for aname, rname in zip(anames, rnames):
        bulk = int(aname.split('_')[1])
        for i in range(bulk):
            try:
                airtime_datasets['overall_bandwidth_bulk'][aname].append(sum(
                    airtime_datasets['bulk'][aname][i * bulk:(i + 1) * bulk]))
                airtime_datasets['overall_bandwidth'][aname].append(
                    airtime_datasets['overall_bandwidth_vr'][aname][i] +
                    airtime_datasets['overall_bandwidth_bulk'][aname][i])
            except IndexError:
                print(f'[-] Someone miss the data: {aname}')

            try:
                resp_datasets['overall_bandwidth_bulk'][rname].append(sum(
                    resp_datasets['bulk'][rname][i * bulk:(i + 1) * bulk]))
                resp_datasets['overall_bandwidth'][rname].append(
                    resp_datasets['overall_bandwidth_vr'][rname][i] +
                    resp_datasets['overall_bandwidth_bulk'][rname][i])
            except IndexError:
                print(f'[-] Someone miss the data: {rname}')

    # Draw the data on matplotlib boxplot
    readable_names = get_human_readable_names(anames)
    total_testcases = int(len(directories) / 2)
    fig, axes = plt.subplots(ncols=total_testcases, sharey=True)
    fig.subplots_adjust(wspace=0)
    fig.suptitle('VR FPS')
    fig.set_size_inches(16, 8)
    for ax, readable, aname, rname in zip(axes, readable_names, anames, rnames):
        ax.boxplot([airtime_datasets['fps'][aname],
                    resp_datasets['fps'][rname]])
        ax.axhline(linewidth=4)
        ax.set_ylim(0, 60)
        ax.set_xticklabels(['airtime', 'resp'], rotation=20)
        ax.set_xlabel(readable)
    fig.savefig('vr_fps.png', bbox_inches='tight', dpi=150)

    fig, axes = plt.subplots(ncols=total_testcases, sharey=True)
    fig.subplots_adjust(wspace=0)
    fig.suptitle('VR Bandwidth')
    fig.set_size_inches(16, 8)
    for ax, readable, aname, rname in zip(axes, readable_names, anames, rnames):
        ax.boxplot([airtime_datasets['bandwidth'][aname],
                    resp_datasets['bandwidth'][rname]])
        ax.axhline(linewidth=4)
        ax.set_ylim(0, 150)
        ax.set_xticklabels(['airtime', 'resp'], rotation=20)
        ax.set_xlabel(readable)
    fig.savefig('vr_bandwidth.png', bbox_inches='tight', dpi=150)

    fig, axes = plt.subplots(ncols=total_testcases, sharey=True)
    cdf_fig, cdf_axes = plt.subplots(math.ceil(total_testcases / 4), 4, sharey=True)
    fig.subplots_adjust(wspace=0)
    fig.suptitle('VR latency')
    fig.set_size_inches(16, 8)
    cdf_fig.suptitle('VR latency CDF')
    cdf_fig.set_size_inches(8, 8)
    for ax, cdf_ax, readable, aname, rname in zip(axes, cdf_axes.reshape(-1),
                                                  readable_names, anames, rnames):
        ax.boxplot([airtime_datasets['latency'][aname],
                    resp_datasets['latency'][rname]])
        ax.axhline(linewidth=4)
        ax.set_ylim(0, 70)
        ax.set_xticklabels(['airtime', 'resp'], rotation=20)
        ax.set_xlabel(readable)
        cdf_ax.set_title(' '.join(readable.split('\n')[-4:-1]))
        cdf_ax.hist(airtime_datasets['latency'][aname], bins='auto', density=True,
                    cumulative=True, histtype='step', color='red', label='airtime',
                    alpha=0.5)
        cdf_ax.hist(resp_datasets['latency'][rname], bins='auto', density=True,
                    cumulative=True, histtype='step', color='blue', label='resp',
                    alpha=0.5)
        cdf_ax.legend(loc='lower right')
    fig.savefig('vr_latency.png', bbox_inches='tight', dpi=150)
    cdf_fig.savefig('vr_latency_cdf.png', bbox_inches='tight', dpi=150)

    fig, axes = plt.subplots(ncols=total_testcases, sharey=True)
    fig.subplots_adjust(wspace=0)
    fig.suptitle('Bulk flow bandwidth')
    fig.set_size_inches(16, 8)
    for ax, readable, aname, rname in zip(axes, readable_names, anames, rnames):
        ax.boxplot([airtime_datasets['overall_bandwidth_bulk'][aname],
                    resp_datasets['overall_bandwidth_bulk'][rname]])
        ax.axhline(linewidth=4)
        ax.set_ylim(0, 140)
        ax.set_xticklabels(['airtime', 'resp'], rotation=20)
        ax.set_xlabel(readable)
    fig.savefig('bulk_flow_bandwidth.png', bbox_inches='tight', dpi=150)

    fig, axes = plt.subplots(ncols=total_testcases, sharey=True)
    fig.subplots_adjust(wspace=0)
    fig.suptitle('Overall Bandwidth')
    fig.set_size_inches(16, 8)
    for ax, readable, aname, rname in zip(axes, readable_names, anames, rnames):
        ax.boxplot([airtime_datasets['overall_bandwidth'][aname],
                    resp_datasets['overall_bandwidth'][rname]])
        ax.axhline(linewidth=4)
        ax.set_ylim(0, 200)
        ax.set_xticklabels(['airtime', 'resp'], rotation=20)
        ax.set_xlabel(readable)
    fig.savefig('overall_bandwidth.png', bbox_inches='tight', dpi=150)


if __name__ == '__main__':
    main(sys.argv[1:])
