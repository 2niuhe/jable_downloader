import time

import config
import model_crawler
import utils
import video_crawler
from config import CONF


def get_need_sync_video_ids(sub):
    # first update cache
    cache_info = utils.get_video_ids_map_from_cache()
    try:
        for item in sub:
            url = item['url']
            cached_video_ids = set(cache_info.get(url, set())) if cache_info else set()
            remote_video_id_set = model_crawler.get_all_video_ids(url, cached_video_ids)
            cache_info[url] = list(remote_video_id_set)
    except Exception:
        raise
    finally:
        utils.update_video_ids_cache(cache_info)

    need_sync_video_ids = set(cache_info[sub[0]['url']])
    for item in sub[1:]:
        url = item['url']
        need_sync_video_ids &= set(cache_info.get(url))
    return need_sync_video_ids


def process_subscription(args):
    if args.add:
        input_urls = args.add
        cur_subscription = []
        for input_url in input_urls:
            model_crawler.input_url_validator(input_url)
            name, _ = model_crawler.get_model_names_and_last_page_num(input_url)
            cur_subscription.append({'url': input_url, 'name': name})

        all_subs = CONF.get('subscriptions', [])

        for subs in all_subs:
            url_group = set()
            for sub_info in subs:
                url_group.add(sub_info['url'])
            if set(input_urls) == url_group:
                print("cur_subscription %s already exists." % subs)
                return

        all_subs.append(cur_subscription)
        CONF['subscriptions'] = all_subs
        config.update_config(CONF)
        print("add cur_subscription success.")
        print(cur_subscription)

    elif args.get:
        print("current subscriptions:\n")
        print(CONF.get('subscriptions', []))
    elif args.sync_videos:
        all_subs = CONF.get('subscriptions', [])
        output_path = CONF.get("outputDir", './')

        local_video_id_set = utils.get_local_video_list(path=output_path)
        base_url = "https://jable.tv/videos/"

        download_inerval = CONF.get("downloadInterval", 1)
        print(all_subs)
        print('\n' + '=' * 10 + '\n')

        for subs in all_subs:
            remote_video_id_set = get_need_sync_video_ids(subs)
            need_sync_video_ids = remote_video_id_set - local_video_id_set
            need_sync_number = len(need_sync_video_ids)

            print("start sync %s remote video to local..." % subs)

            for index, video_id in enumerate(need_sync_video_ids):
                print("该订阅需同步视频 %s 个 / 剩余 %s 个 " % (need_sync_number, need_sync_number - index))
                download_url = base_url + video_id + '/'
                print(download_url)
                video_crawler.download_by_video_url(download_url)

                local_video_id_set.add(video_id)
                if index < len(need_sync_video_ids) - 1:
                    print("sleep %s seconds" % download_inerval)
                    time.sleep(download_inerval)
        print("sync success.")


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
