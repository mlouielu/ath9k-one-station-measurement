import sys
import glob
import measure_netlink


TARGET_MAC = '24:18:1d:71:71:c8'


def main(filenames):
    target_enqs = []
    for filename in filenames:
        with open(filename) as f:
            diffs = measure_netlink.calculate_diffs(f.read().strip().split('\n'))
            enq_diffs = diffs['enq']
            target_enqs.extend(enq_diffs[TARGET_MAC])

            print(measure_netlink.get_result_text('target', enq_diffs[TARGET_MAC]))
    print(measure_netlink.get_result_text('target', target_enqs))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        directory = sys.argv[1:]
        for d in directory:
            files = glob.glob(f'{d.strip("/")}/output_*')
            print(f'[*] {d}')
            main(files)
            print()
    else:
        files = glob.glob('output_*')
        main(files)
