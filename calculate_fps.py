import sys
import statistics
import glob
import pprint


def get_fps_data(lines):
    data = []
    for i in lines:
        timestamp, fps, bandwidth = i.strip().split()
        if float(bandwidth) > 1.0:
            data.append(int(fps.split('/')[1]))
    return data


def calculate_fps_statistics(fps):
    d = {
        'mean': statistics.mean(fps),
        'median': statistics.median(fps),
        'stdev': statistics.stdev(fps),
    }
    return d


def main(files):
    all_fps = []
    print('FPS Statistics for each set')
    for i in files:
        with open(i) as f:
            fps_data = get_fps_data(f.readlines())
            fps_statistics = calculate_fps_statistics(fps_data)
            print(fps_statistics)

            all_fps.extend(fps_data)

    print('All FPS data in this sets')
    print(calculate_fps_statistics(all_fps))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = glob.glob('*.txt')
    main(files)
