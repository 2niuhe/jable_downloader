from bs4 import BeautifulSoup

import utils


def input_url_validator(tag_url):
    if "from=" in tag_url or "videos/" in tag_url:
        raise Exception("input url is not valid. url cannot contain page number")


def get_model_names_and_last_page_num(url):
    res = utils.requests_with_retry(url)

    last_page_num = 1
    model_name = "unknown"

    content = res.content
    soup = BeautifulSoup(content, 'html.parser')

    model_name_item = soup.select('#list_videos_common_videos_list > section > div > div > div > h2')
    if model_name_item:
        model_name = model_name_item[0].text
    elif "jable.tv/search/" in url:
        model_name = url.replace("https://jable.tv/search/", "")[:-1]
    else:
        raise Exception("cannot get name of subcription")
    page_items = soup.select('.pagination>.page-item>.page-link')
    last_item = page_items[-1].get('data-parameters') if page_items else []
    if last_item:
        page_num = last_item.split(":")[-1]
        if page_num.isdigit():
            last_page_num = int(last_item.split(":")[-1])

    return model_name, last_page_num


def get_model_total_video_num(url):
    res = utils.requests_with_retry(url)
    content = res.content
    soup = BeautifulSoup(content, 'html.parser')

    total_num = 0
    foo = soup.select('span.inactive-color')
    if foo:
        if foo[0].text.split()[0].isdigit():
            total_num = int(foo[0].text.split()[0])

    return total_num


def get_all_video_ids(url, cached_ids_set=None):
    tag_name, last_page_num = get_model_names_and_last_page_num(url)

    total_video_num = 0
    if cached_ids_set and last_page_num > 10:
        total_video_num = get_model_total_video_num(url)

    if cached_ids_set and len(cached_ids_set) == total_video_num:
        print("远端无更新，索引和本地缓存一致，跳过抓取索引")
        return cached_ids_set

    video_ids = set()
    for page_num in range(1, last_page_num + 1):
        page_url = url + "?from=%s" % page_num
        print("\r抓取 %s 第 %s 页 共 %s 页" % (tag_name, page_num, last_page_num), end="", flush=True)

        res = utils.requests_with_retry(page_url, retry=20)

        content = res.content
        soup = BeautifulSoup(content, 'html.parser')
        a_tags = soup.select('div.img-box>a')
        for a_tag in a_tags:
            video_ids.add(a_tag['href'].split('/')[-2])

        # allow 1% miss
        if cached_ids_set and total_video_num > 1000 and \
                abs((total_video_num - len(cached_ids_set))) * 100 < len(cached_ids_set):
            print("缓存索引和远端误差低于百分之一, 本地 %s 远端 %s 不更新 %s 索引\n" % (len(cached_ids_set), total_video_num, url))
            print("新增 %s 个索引" % len(video_ids - cached_ids_set))
            video_ids |= cached_ids_set
            break

        if cached_ids_set and total_video_num > 0:
            if len(video_ids | cached_ids_set) >= total_video_num:
                video_ids |= cached_ids_set
                print("和缓存索引合并生效, 退出抓取")
                break

    print('%s => 获取到 %s 个影片' % (tag_name, len(video_ids)))
    return video_ids
