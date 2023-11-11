#!/usr/bin/python
# coding: utf-8

import argparse
from executor import process_subscription, process_videos

parser = argparse.ArgumentParser(description="jable downloader")

sub_parser = parser.add_subparsers()

video_parser = sub_parser.add_parser("videos", help="download video by urls")
video_parser.add_argument("urls", metavar='N', type=str, nargs='+',
                          help="jable video urls to download")

video_parser.set_defaults(func=process_videos)



if __name__ == '__main__':
    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        exit()

    args.func(args)
