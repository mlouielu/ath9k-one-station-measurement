import sys
import statistics
import glob
import pprint


def get_data(lines):
    fps_data = []
    bandwidth_data = []
    for i in lines:
        timestamp, fps, bandwidth = i.strip().split()
        if float(bandwidth) > 1.0:
            fps_data.append(int(fps.split('/')[1]))
            bandwidth_data.append(float(bandwidth))
    return fps_data, bandwidth_data


def calculate_fps_statistics(fps):
    d = {
        'mean': statistics.mean(fps),
        'median': statistics.median(fps),
        'stdev': statistics.stdev(fps),
    }
    return d


def main(files):
    all_fps = []
    all_bandwidth = []
    print('FPS Statistics for each set')
    for i in files:
        with open(i) as f:
            data = f.readlines()
            fps, bandwidth = get_data(data)
            fps_statistics = calculate_fps_statistics(fps)
            print(fps_statistics)

            all_fps.extend(fps)
            all_bandwidth.extend(bandwidth)

    print('All FPS data in this sets')
    print(calculate_fps_statistics(all_fps))

    print('All VR Bandwidth in this sets')
    print(calculate_fps_statistics(all_bandwidth))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = glob.glob('*.txt')
    main(files)
