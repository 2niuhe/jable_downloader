#!/usr/bin/python
# coding: utf-8

import argparse
from executor import process_videos

parser = argparse.ArgumentParser(description="m3u8/jable/missav downloader")
parser.add_argument("urls", metavar='N', type=str, nargs='+',
                          help="urls (m3u8/jable/missav...)")
parser.add_argument("--refer", type=str, default='',
                           help="refer url, for example: https://missav.com")
parser.set_defaults(func=process_videos)

if __name__ == '__main__':
    args = None
    try:
        args = parser.parse_args()
        if not hasattr(args, 'func'):
            parser.print_help()
            exit(1)
    except:
        parser.print_help()
        exit(1)

    args.func(args)
