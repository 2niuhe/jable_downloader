import re
import time

import config
import utils
import video_crawler

CONF = config.CONF

def url_validator(url: str) -> bool:
    if url.endswith('.m3u8'):
        return True
    if url.startswith('https://jable.tv/videos/'):
        return True
    if url.startswith('https://missav.com/'):
        return True
    return False

def process_videos(args):
    video_urls = []
    for url in args.urls:
        if not url_validator(url):
            raise Exception('%s is not supported.' % url)

    for url in args.urls:
        if 'jable' in url and not url.endswith('/'):
            video_urls.append(url+'/')
        else:
            video_urls.append(url)

    output_path = CONF.get("outputDir", './')
    local_video_id_set = utils.get_local_video_list(path=output_path)
    ignore_video_ids = local_video_id_set

    re_extractor = re.compile(r"[a-zA-Z0-9]{2,}-\d{3,}")
    refer_url = args.refer
    for video_url in video_urls:
        re_res = re_extractor.search(video_url)
        if re_res:
            video_id = re_res.group(0)
            if video_id and video_id in ignore_video_ids:
                print("视频 %s 已经下载，跳过该视频" % video_url)
                continue
            ignore_video_ids.add(video_id)
        if video_url.endswith('.m3u8') or video_url.endswith('.m3u8/'):
            video_crawler.download_m3u8_directly(video_url, refer_url)
        else:
            video_crawler.download_jable_by_video_url(video_url, refer_url)
