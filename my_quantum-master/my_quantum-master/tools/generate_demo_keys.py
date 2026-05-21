#!/usr/bin/env python3
"""Generate demo quantum keys and physical-layer keys.

Outputs:
- QKD_Keys/a.txt: one 64-hex quantum key per line.
- Physical_Keys/b.txt on the gateway: physical_key_id,32hex.
- Physical_Keys/b.txt on the cloud center: the same physical key lines.
"""

import argparse
import os
import secrets
import time
from datetime import datetime


def default_paths():
    gateway_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(os.path.dirname(gateway_root))
    cloud_root = os.path.join(project_root, 'qkd_center-master', 'qkd_center-master')
    return {
        'quantum_file': os.path.join(gateway_root, 'QKD_Keys', 'a.txt'),
        'gateway_physical_file': os.path.join(gateway_root, 'Physical_Keys', 'b.txt'),
        'cloud_physical_file': os.path.join(cloud_root, 'Physical_Keys', 'b.txt'),
    }


def append_line(path, line):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def generate_batch(paths, batch_size):
    quantum_lines = [secrets.token_hex(32) for _ in range(batch_size)]
    physical_lines = []
    stamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    for index in range(batch_size):
        key_id = f'phy-{stamp}-{secrets.token_hex(4)}-{index:04d}'
        physical_lines.append(f'{key_id},{secrets.token_hex(16)}')

    for line in quantum_lines:
        append_line(paths['quantum_file'], line)
    for line in physical_lines:
        append_line(paths['gateway_physical_file'], line)
        append_line(paths['cloud_physical_file'], line)

    return len(quantum_lines), len(physical_lines)


def main():
    paths = default_paths()
    parser = argparse.ArgumentParser(description='Generate demo QKD and physical-layer keys.')
    parser.add_argument('--quantum-file', default=paths['quantum_file'])
    parser.add_argument('--gateway-physical-file', default=paths['gateway_physical_file'])
    parser.add_argument('--cloud-physical-file', default=paths['cloud_physical_file'])
    parser.add_argument('--batch-size', type=int, default=5)
    parser.add_argument('--interval-sec', type=float, default=5.0)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()

    output_paths = {
        'quantum_file': args.quantum_file,
        'gateway_physical_file': args.gateway_physical_file,
        'cloud_physical_file': args.cloud_physical_file,
    }

    while True:
        quantum_count, physical_count = generate_batch(output_paths, args.batch_size)
        print(
            f"Generated {quantum_count} quantum key(s) and {physical_count} physical key(s): "
            f"{output_paths['quantum_file']}, {output_paths['gateway_physical_file']}, "
            f"{output_paths['cloud_physical_file']}"
        )
        if args.once:
            break
        time.sleep(args.interval_sec)


if __name__ == '__main__':
    main()
