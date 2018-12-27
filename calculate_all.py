import os
import sys


def main(directory):
    print(f'[*] directory: {directory}')
    os.system(f'python calculate_fps.py {directory}')
    print('=' * 30)
    os.system(f'python calculate_bulk_bandwidth.py {directory}')
    print('=' * 30)
    os.system(f'python calculate_latency.py {directory}')
    print()


if __name__ == '__main__':
    for d in sys.argv[1:]:
        main(d)
