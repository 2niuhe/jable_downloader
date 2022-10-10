# coding: utf-8

import argparse
from executor import process_subscription, process_videos

parser = argparse.ArgumentParser(description="jable downloader")

sub_parser = parser.add_subparsers()

video_parser = sub_parser.add_parser("videos", help="download video by urls")
video_parser.add_argument("urls", metavar='N', type=str, nargs='+',
                          help="jable video urls to download")

video_parser.set_defaults(func=process_videos)

models_parser = sub_parser.add_parser("subscription",
                                      help="subscribe some topic(models or tags)/sync videos from subscriptions")

models_parser.add_argument("--add", type=str, default="",
                           help="add subscription by single url, support models/tags")
models_parser.add_argument("--get", action='store_true',
                           help="get current subscription")
models_parser.add_argument("--sync-videos", action='store_true',
                           help="download all subscription related videos")

models_parser.set_defaults(func=process_subscription)


if __name__ == '__main__':
    args = parser.parse_args()

    args.func(args)

