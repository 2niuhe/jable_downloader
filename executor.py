import re
import time

import config
import utils
import video_crawler

CONF = config.CONF

def process_videos(args):
    video_urls = []
    for url in args.urls:
        if "videos" not in url:
            raise Exception("only support video url")
        if not url.endswith('/'):
            video_urls.append(url+'/')
        else:
            video_urls.append(url)

    output_path = CONF.get("outputDir", './')
    local_video_id_set = utils.get_local_video_list(path=output_path)
    block_video_ids = {str.lower(video_id) for video_id in config.CONF.get("videoIdBlockList", [])}
    ignore_video_ids = local_video_id_set | block_video_ids

    re_extractor = re.compile(r"[a-zA-Z0-9]{2,}-\d{3,}")

    for video_url in video_urls:
        re_res = re_extractor.search(video_url)
        if re_res:
            video_id = re_res.group(0)
            if video_id and video_id in ignore_video_ids:
                print("视频 %s 已经下载，跳过该视频" % video_url)
                continue
            ignore_video_ids.add(video_id)
        video_crawler.download_by_video_url(video_url)
