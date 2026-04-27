#!/usr/bin/env python3

"""S25 health summary"""

import subprocess

def main():
    print("GPU status:", subprocess.check_output(['nvidia-smi']).decode())
    print("Disk usage:", subprocess.check_output(['df', '-h']).decode())
    print("Cron jobs:")
    with open('/etc/crontab', 'r') as f:
        for line in f:
