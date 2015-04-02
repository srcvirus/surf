#!/usr/bin/python

import argparse
import sys
import yaml
import digitalocean
from surf_fs import SurfFS
from fuse import FUSE


def main():
    parser = argparse.ArgumentParser(
        description="File system interface for DigitalOcean droplets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', help='Configuration file name',
                        default='/etc/surf.conf.yaml')
    parser.add_argument(
        '--mpoint',
        help='Mount point of the file system',
        required=True)
    parser.add_argument(
        '--storage',
        help='Backing storage for easy passthrough',
        required=True)
    args = parser.parse_args()
    configuration = yaml.load(open(args.config))
    personal_token = configuration['personal_token']
    FUSE(SurfFS(personal_token, args.mpoint, args.storage), args.mpoint,
         foreground=True)

if __name__ == "__main__":
    main()
