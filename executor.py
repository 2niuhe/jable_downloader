import time

import config
import model_crawler
import utils
import video_crawler
from config import CONF


def process_subscription(args):
    if args.add:
        input_url = args.add
        model_crawler.input_url_validator(input_url)
        name, _ = model_crawler.get_model_names_and_last_page_num(input_url)
        all_subs = CONF.get('subscriptions', [])
        all_subs_urls = {subs['url'] for subs in all_subs}

        subs = {'url': input_url, 'name': name}
        if input_url not in all_subs_urls:
            all_subs.append(subs)
            CONF['subscriptions'] = all_subs
            config.update_config(CONF)
            print("add subscription success.")
            print(subs)
        else:
            print("subscription already exists.")
        # print(model_crawler.get_all_video_links(input_url))
    elif args.get:
        print("current subscriptions:\n")
        print(CONF.get('subscriptions', []))
    elif args.sync_videos:
        all_subs = CONF.get('subscriptions', [])
        output_path = CONF.get("outputDir", './')

        local_video_id_set = utils.get_local_video_list(path=output_path)
        base_url = "https://jable.tv/videos/"

        download_inerval = CONF.get("downloadInterval", 1)

        for subs in all_subs:

            remote_video_id_set = model_crawler.get_all_video_ids(subs['url'])
            need_sync_video_ids = remote_video_id_set - local_video_id_set

            print("start sync %s remote video to local..." % subs['name'])
            print("need sync video number is %s " % len(need_sync_video_ids))
            for video_id in need_sync_video_ids:
                download_url = base_url + video_id + '/'
                video_crawler.download_by_video_url(download_url)

                local_video_id_set.add(video_id)
                print("sleep %s seconds" % download_inerval)
                time.sleep(download_inerval)


def process_videos(args):
    video_urls = []
    for url in args.urls:
        if "videos" not in url:
            raise Exception("only support video url")
        if not url.endswith('/'):
            video_urls.append(url+'/')
        else:
            video_urls.append(url)
    for video_url in video_urls:
        video_crawler.download_by_video_url(video_url)
