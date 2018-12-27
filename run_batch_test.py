import os
import sys
import subprocess
import requests
import time
import tomlkit


HOST = '192.168.7.222'
PORT = '5000'


def set_quality(quality):
    while True:
        try:
            requests.get(f'http://{HOST}:{PORT}/change_trinus_vr_image_quality/{quality}')
            break
        except requests.exceptions.ConnectionError:
            print('[-] Cannot setup Windows Trinus VR Quality')
            time.sleep(1)


def set_compress(level):
    while True:
        try:
            requests.get(f'http://{HOST}:{PORT}/change_trinus_vr_compress_level/{level}')
            break
        except requests.exceptions.ConnectionError:
            print('[-] Cannot setup Windows Trinus VR Compress Level')
            time.sleep(1)


def set_priority_ac(ac):
    # Reset mangle forward rule
    subprocess.Popen(['sudo', 'iptables', '-t',
                      'mangle', '-D', 'FORWARD', '1']).communicate()
    dscp_class = None
    if ac == 'AC_VO':
        dscp_class = 'cs7'
    elif ac == 'AC_VI':
        dscp_class = 'cs5'

    if dscp_class:
        subprocess.Popen(['sudo', 'iptables', '-t',
                          'mangle', '-A', 'FORWARD',
                          '-s', HOST, '-j', 'DSCP',
                          '--set-dscp-class', dscp_class]).communicate()


def run_batch_test_replace_vr_by_iperf(config):
    for ac in config['cases']['priority_dscp']:
        set_priority_ac(ac)
        for bulk_flow in config['cases']['bulk_flow']:
            for loop in range(config['cases']['loop']):
                filename = f'batch_vr_replace_by_iperf_{ac}_bulk_{bulk_flow}_{loop}'
                print('[*] Start the test')
                subprocess.Popen(['./run_trinus_vr_test.py',
                                  '--pid', config['trinusvr']['pid'],
                                  '--address', config['trinusvr']['address'],
                                  '--output', filename,
                                  '--iperf', str(bulk_flow),
                                  '--replace-vr',
                                  '--time', str(config['cases']['time'])]).communicate()


def run_batch_test(config):
    for ac in config['cases']['priority_dscp']:
        set_priority_ac(ac)
        for bulk_flow in config['cases']['bulk_flow']:
            for quality in config['cases']['image_quality']:
                for compress_level in config['cases']['compress_level']:
                    for loop in range(config['cases']['loop']):
                        # Reset iperf
                        print('[*] Reset iperf')
                        subprocess.check_call('./reset_iperf3.sh')

                        print('[*] Reset Android Trinus VR...')
                        for i in range(3):
                            subprocess.Popen(['./open_trinusvr_android.sh'],
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL).communicate()

                        filename = f'batch_{ac}_{quality}_compress_{compress_level}_bulk_{bulk_flow}_{loop}'
                        print(ac, quality, compress_level, bulk_flow)

                        print('[*] Setting Trinus VR Quality and Compress Level on Windows')
                        set_quality(quality)
                        set_compress(compress_level)

                        print('[*] Start the test')
                        # subprocess.Popen(['./run_bulk_flow.sh', str(bulk_flow), filename])
                        subprocess.Popen(['./run_trinus_vr_test.py',
                                          '--pid', config['trinusvr']['pid'],
                                          '--address', config['trinusvr']['address'],
                                          '--output', filename,
                                          '--iperf', str(bulk_flow),
                                          '--time', str(config['cases']['time'])]).communicate()


def get_count_dirname(name):
    count = 0
    while True:
        dirname = f'{name}_{count:03d}'
        if not os.path.isdir(dirname):
            return dirname
        count += 1


def get_result_dirname(config, low, high, resptime, atf, ia):
    vriperf = config['cases']['replace_vr_by_iperf']
    bulk = config['cases']['bulk_flow'][0]  # FIXME: can only deal with one cases

    dirname = f'bulk_{bulk}_' + ('vriperf_' if vriperf else 'vr_')
    dirname += f'atf_{atf}_ia_{ia}_' + ('resptime_' if resptime else 'airtime_')
    dirname += f'{low:04d}_{high:04d}'
    return dirname


def move_test_results_to_dir(config, low, high, resptime, atf, ia):
    dirname = get_result_dirname(config, low, high, resptime, atf, ia)
    dirname = get_count_dirname(dirname)
    os.system(f'mkdir {dirname}')
    os.system(f'./move_test_files_to.sh {dirname}')


def run_environment(config):
    for quantum_low in config['environment']['airtime_quantum_low']:
        for quantum_high in config['environment']['airtime_quantum_high']:
            subprocess.check_call(
                f'sudo python /root/set_airtime_quantum.py {quantum_low} {quantum_high}'.split())
            for resptime in config['environment']['resptime']:
                for atf in config['environment']['atf']:
                    for ia in config['environment']['ia']:
                        if (config['environment']['airtime_same'] and
                                quantum_high != quantum_low):
                            continue

                        # Check if skip the cases
                        dirname = get_result_dirname(config,
                                                     quantum_low,
                                                     quantum_high,
                                                     resptime, atf, ia)
                        if (config['environment']['skip_exist'] and
                                os.path.isdir(f'{dirname}_'
                                              f'{config["environment"]["no"]:03d}')):
                            print(f'[*] Skip case: {dirname}')
                            continue

                        # Setup wifi environment
                        subprocess.check_call(
                            'sudo python /root/set_responsible_airtime.py '
                            f'{resptime} {atf} {ia}'.split())

                        # Reset airtime
                        subprocess.check_call(
                            'sudo python /root/reset_airtime.py'.split())

                        # Real test cases
                        if not config['cases']['replace_vr_by_iperf']:
                            run_batch_test(config)
                        else:
                            run_batch_test_replace_vr_by_iperf(config)

                        move_test_results_to_dir(config,
                                                 quantum_low, quantum_high,
                                                 resptime, atf, ia)


if __name__ == '__main__':
    config_filename = sys.argv[1]
    with open(config_filename) as f:
        config = tomlkit.parse(f.read())

    run_environment(config)
