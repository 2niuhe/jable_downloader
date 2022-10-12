import requests
import time
from bs4 import BeautifulSoup

from config import headers


def input_url_validator(tag_url):
    if "from=" in tag_url or "videos/" in tag_url:
        raise Exception("input url is not valid. url cannot contain page number")


def get_model_names_and_last_page_num(url):
    res = requests.get(url, headers=headers, timeout=20)
    last_page_num = 1
    if res.status_code == 200:
        content = res.content
        soup = BeautifulSoup(content, 'html.parser')

        model_name = soup.select('#list_videos_common_videos_list > section > div > div > div > h2')[0].text
        page_items = soup.select('.pagination>.page-item>.page-link')
        last_item = page_items[-1].get('data-parameters')
        if last_item:
            page_num = last_item.split(":")[-1]
            if page_num.isdigit():
                last_page_num = int(last_item.split(":")[-1])
    return model_name, last_page_num


def get_model_total_video_num(url):
    res = requests.get(url, headers=headers, timeout=20)
    if res.status_code == 200:
        content = res.content
        soup = BeautifulSoup(content, 'html.parser')

        totall_num = 0
        foo = soup.select('span.inactive-color')
        if foo:
            if foo[0].text.split()[0].isdigit():
                totall_num = int(foo[0].text.split()[0])

    return totall_num


def get_all_video_ids(url, cached_ids_set=None):
    tag_name, last_page_num = get_model_names_and_last_page_num(url)
    if not url.endswith('/'):
        url = url + '/'

    total_video_num = 0
    if cached_ids_set and last_page_num > 4:
        total_video_num = get_model_total_video_num(url)

    video_ids = set()
    for page_num in range(1, last_page_num + 1):
        page_url = url + "?from=%s" % page_num
        print("\r抓取 %s 第 %s 页 共 %s 页" % (tag_name, page_num, last_page_num), end="", flush=True)

        if page_num % 10 == 0:
            time.sleep(10)

        try:
            res = requests.get(page_url, headers=headers, timeout=20)
        except:
            time.sleep(30)
            res = requests.get(page_url, headers=headers, timeout=20)

        if res.status_code == 200:
            content = res.content
            soup = BeautifulSoup(content, 'html.parser')
            a_tags = soup.select('div.img-box>a')
            for a_tag in a_tags:
                video_ids.add(a_tag['href'].split('/')[-2])

        # allow 1% miss
        if cached_ids_set and total_video_num > 1000 and \
                abs((total_video_num - len(cached_ids_set))) * 100 < len(cached_ids_set):
            print("缓存索引和远端误差低于百分之一, 本地 %s 远端 %s 不更新 %s 索引\n" % (len(cached_ids_set), total_video_num, url))
            video_ids |= cached_ids_set
            break

        if cached_ids_set and total_video_num > 0:
            if len(video_ids | cached_ids_set) >= total_video_num:
                video_ids |= cached_ids_set
                print("和缓存索引合并生效, 退出抓取")
                break

    print('%s => 获取到 %s 个影片' % (tag_name, len(video_ids)))
    return video_ids
