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
    if ac == 'AC_BE':
        subprocess.Popen(['sudo', 'iptables', '-t',
                          'mangle', '-D', 'FORWARD', '1']).communicate()
    elif ac == 'AC_VO':
        subprocess.Popen(['sudo', 'iptables', '-t',
                          'mangle', '-A', 'FORWARD',
                          '-s', HOST, '-j', 'DSCP',
                          '--set-dscp-class', 'cs7']).communicate()


def run_batch_test(config):
    for ac in config['cases']['priority_dscp']:
        set_priority_ac(ac)
        for bulk_flow in config['cases']['bulk_flow']:
            for quality in config['cases']['image_quality']:
                for compress_level in config['cases']['compress_level']:
                    for loop in range(config['cases']['loop']):
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


if __name__ == '__main__':
    config_filename = sys.argv[1]
    with open(config_filename) as f:
        config = tomlkit.parse(f.read())

    run_batch_test(config)
