import concurrent.futures
import copy
import os
import re
import shutil
import time
from functools import partial

import cloudscraper
import m3u8
from Crypto.Cipher import AES
from bs4 import BeautifulSoup

import utils
from config import CONF
from utils import deleteM3u8
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
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    query_params = dict()
    proxies_config = CONF.get('proxies', None)
    if proxies_config and 'http' in proxies_config and 'https' in proxies_config:
        query_params['proxies'] = proxies_config

    htmlfile = cloudscraper.create_scraper(browser='chrome', delay=20).get(url, **query_params)
    video_full_name = get_video_full_name(video_id, htmlfile)

    if os.path.exists(os.path.join(output_dir, video_full_name + '.mp4')):
        print(video_full_name + "already exist, skip download.")
        return
    print("start download %s " % video_full_name)
    tmp_dir_name = os.path.join(output_dir, video_id)
    if not os.path.exists(tmp_dir_name):
        os.makedirs(tmp_dir_name)

    result = re.search("https://.+m3u8", htmlfile.text)
    m3u8url = result[0]

    m3u8urlList = m3u8url.split('/')
    m3u8urlList.pop(-1)
    downloadurl = '/'.join(m3u8urlList)

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

    tsList = []
    for seg in m3u8obj.segments:
        tsUrl = downloadurl + '/' + seg.uri
        tsList.append(tsUrl)

    if m3u8uri:
        m3u8keyurl = downloadurl + '/' + m3u8uri

        response = utils.requests_with_retry(m3u8keyurl)
        contentKey = response.content

        vt = m3u8iv.replace("0x", "")[:16].encode()

        ci = AES.new(contentKey, AES.MODE_CBC, vt)
    else:
        ci = ''

    deleteM3u8(tmp_dir_name)

    prepareCrawl(ci, tmp_dir_name, tsList)

    merge_mp4(tmp_dir_name, output_dir, video_full_name, tsList)

    if CONF.get("downloadVideoCover", True):
        get_cover(html_file=htmlfile, folder_path=output_dir)

    shutil.rmtree(tmp_dir_name)


def scrape(ci, folderPath, downloadList, urls):
    os.path.split(urls)
    fileName = urls.split('/')[-1][0:-3]
    saveName = os.path.join(folderPath, fileName + ".mp4")
    if os.path.exists(saveName):
        print('\r当前目标: {0} 已下载, 故跳过...剩余 {1} 个'.format(
            urls.split('/')[-1], len(downloadList)), end='', flush=True)
        downloadList.remove(urls)
    else:
        response = utils.requests_with_retry(urls, retry=5)

        if not response:
            print('当前目标: {0} 下载失败, 继续下载剩余内容...剩余 {1} 个'.format(
            urls.split('/')[-1], len(downloadList)))
            return

        content_ts = response.content
        if ci:
            content_ts = ci.decrypt(content_ts)
        with open(saveName, 'ab') as f:
            f.write(content_ts)

        downloadList.remove(urls)
        print('\r当前下载: {0} , 剩余 {1} 个, status code: {2}'.format(
            urls.split('/')[-1], len(downloadList), response.status_code), end='', flush=True)


def prepareCrawl(ci, folderPath, tsList):
    downloadList = copy.deepcopy(tsList)

    start_time = time.time()
    print('开始下载 ' + str(len(downloadList)) + ' 个文件..', end='')
    print('预计等待时间: {0:.2f} 分钟 视视频大小和网络速度而定)'.format(len(downloadList) / 150))

    startCrawl(ci, folderPath, downloadList)

    end_time = time.time()
    print('\n消耗 {0:.2f} 分钟 同步1个视频完成 !'.format((end_time - start_time) / 60))


def startCrawl(ci, folderPath, downloadList):
    round = 0
    while (downloadList != []):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(partial(scrape, ci, folderPath,
                                 downloadList), downloadList)
        round += 1
        print(f', round {round}')
