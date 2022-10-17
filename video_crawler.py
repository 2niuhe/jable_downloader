import concurrent.futures
import copy
import os
import re
import time
from functools import partial

import m3u8
from Crypto.Cipher import AES
from bs4 import BeautifulSoup

import utils
from config import CONF
from utils import delete_m3u8
from utils import merge_mp4


def get_video_full_name(video_id, html_file):
    soup = BeautifulSoup(html_file.text, "html.parser")
    video_full_name = video_id

    for meta in soup.find_all("meta"):
        meta_content = meta.get("content")
        if not meta_content:
            continue
        if video_id not in meta_content.lower():
            continue
        video_full_name = meta_content
        break

    if len(video_full_name.encode()) > 248:
        video_full_name = video_full_name[:50]

    return video_full_name


def get_cover(html_file, folder_path):
    soup = BeautifulSoup(html_file.text, "html.parser")
    cover_name = f"{os.path.basename(folder_path)}.jpg"
    cover_path = os.path.join(folder_path, cover_name)
    for meta in soup.find_all("meta"):
        meta_content = meta.get("content")
        if not meta_content:
            continue
        if "preview.jpg" not in meta_content:
            continue
        try:
            r = utils.requests_with_retry(meta_content)
            with open(cover_path, "wb") as cover_fh:
                r.raw.decode_content = True
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        cover_fh.write(chunk)
        except Exception as e:
            print(f"unable to download cover: {e}")

    print(f"cover downloaded as {cover_name}")


def download_by_video_url(url):
    video_id = url.split('/')[-2]

    output_dir = CONF.get("outputDir")

    if not output_dir or output_dir == "./":
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)

    page_res = utils.cloudscraper_requests_get(url, retry=5)

    video_full_name = get_video_full_name(video_id, page_res)

    if os.path.exists(os.path.join(output_dir, video_full_name + '.mp4')):
        print(video_full_name + " 已经存在，跳过下载")
        return
    print("开始下载 %s " % video_full_name)
    tmp_dir_name = os.path.join(output_dir, video_id)

    os.makedirs(tmp_dir_name, exist_ok=True)

    result = re.search("https://.+m3u8", page_res.text)
    m3u8url = result[0]

    m3u8url_list = m3u8url.split('/')
    m3u8url_list.pop(-1)
    download_url = '/'.join(m3u8url_list)

    m3u8file = os.path.join(tmp_dir_name, video_id + '.m3u8')
    response = utils.requests_with_retry(m3u8url)
    with open(m3u8file, 'wb') as f:
        f.write(response.content)

    m3u8obj = m3u8.load(m3u8file)
    m3u8uri = ''
    m3u8iv = ''

    for key in m3u8obj.keys:
        if key:
            m3u8uri = key.uri
            m3u8iv = key.iv

    ts_list = []
    for seg in m3u8obj.segments:
        ts_url = download_url + '/' + seg.uri
        ts_list.append(ts_url)

    if m3u8uri:
        m3u8key_url = download_url + '/' + m3u8uri

        response = utils.requests_with_retry(m3u8key_url)
        content_key = response.content

        vt = m3u8iv.replace("0x", "")[:16].encode()

        ci = AES.new(content_key, AES.MODE_CBC, vt)
    else:
        ci = ''

    delete_m3u8(tmp_dir_name)

    prepare_crawl(ci, tmp_dir_name, ts_list)

    merge_mp4(tmp_dir_name, output_dir, video_full_name, ts_list)

    if CONF.get("downloadVideoCover", True):
        get_cover(html_file=page_res, folder_path=output_dir)


def scrape(ci, folder_path, download_list, urls):
    os.path.split(urls)
    file_name = urls.split('/')[-1][0:-3]
    save_filename = os.path.join(folder_path, file_name + ".mp4")
    if os.path.exists(save_filename):
        print('\r当前目标: {0} 已下载, 故跳过...剩余 {1} 个'.format(
            urls.split('/')[-1], len(download_list)), end='', flush=True)
        download_list.remove(urls)
    else:
        try:
            ignore_proxy = CONF.get("save_vpn_traffic")
            response = utils.requests_with_retry(urls, retry=5, ignore_proxy=ignore_proxy)
        except Exception as e:
            print(e)
            print('当前目标: {0} 下载失败, 继续下载剩余内容...剩余 {1} 个'.format(
                urls.split('/')[-1], len(download_list)))
            return

        content_ts = response.content
        if ci:
            content_ts = ci.decrypt(content_ts)
        with open(save_filename, 'ab') as f:
            f.write(content_ts)

        download_list.remove(urls)
        print('\r当前下载: {0} , 剩余 {1} 个'.format(
            urls.split('/')[-1], len(download_list)), end='', flush=True)


def prepare_crawl(ci, folder_path, ts_list):
    download_list = copy.deepcopy(ts_list)

    start_time = time.time()
    print('开始下载 ' + str(len(download_list)) + ' 个文件..', end='')
    print('预计等待时间: {0:.2f} 分钟 视视频大小和网络速度而定)'.format(len(download_list) / 150))

    start_crawl(ci, folder_path, download_list)

    end_time = time.time()
    print('\n消耗 {0:.2f} 分钟 同步1个视频完成 !'.format((end_time - start_time) / 60))


def start_crawl(ci, folder_path, download_list):
    down_round = 0
    while download_list:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(partial(scrape, ci, folder_path,
                                 download_list), download_list)
        down_round += 1
        # print(f', round {down_round}')
