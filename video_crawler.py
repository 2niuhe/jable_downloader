import concurrent.futures
import io
import os
import pathlib
import re
import shutil
import time
from functools import partial

import m3u8
from Crypto.Cipher import AES
from bs4 import BeautifulSoup

import utils
from config import CONF

avoid_chars = ['/', '\\', '\t', '\n', '\r']

BUFFER_SIZE = 1024 * 1024 * 20  # 20MB
MAX_WORKER = 8

def get_video_full_name(video_id, html_str):
    soup = BeautifulSoup(html_str, "html.parser")
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

    # remove avoid char
    for char in avoid_chars:
        video_full_name = video_full_name.replace(char, '')

    return video_full_name


def get_cover(html_str, folder_path):
    soup = BeautifulSoup(html_str, "html.parser")
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


def prepare_output_dir():
    output_dir = CONF.get("outputDir")
    if not output_dir or output_dir == "./":
        output_dir = os.getcwd()
    else:
        os.makedirs(output_dir, exist_ok=True)
    return output_dir


def mv_video_and_download_cover(output_dir, video_id, video_full_name, html_str):
    src_file_name = os.path.join(output_dir, video_full_name + '.mp4')
    dest_dir_name = output_dir
    output_format = CONF.get('outputFileFormat', '')
    if output_format == 'id/id.mp4':
        dest_dir_name = os.path.join(output_dir, video_id)
        os.makedirs(dest_dir_name, exist_ok=True)
        dst_filename = os.path.join(dest_dir_name, video_id + '.mp4')
        shutil.move(src_file_name, dst_filename)
    elif output_format == 'id/title.mp4':
        dest_dir_name = os.path.join(output_dir, video_id)
        os.makedirs(dest_dir_name, exist_ok=True)
        dst_filename = os.path.join(dest_dir_name, video_full_name + '.mp4')
        shutil.move(src_file_name, dst_filename)
    elif output_format == 'id.mp4':
        dst_filename = os.path.join(output_dir, video_id + '.mp4')
        shutil.move(src_file_name, dst_filename)

    if CONF.get("downloadVideoCover", True):
        get_cover(html_str, folder_path=dest_dir_name)


def download_by_video_url(url):
    video_id = url.split('/')[-2]

    output_dir = prepare_output_dir()

    page_str = utils.scrapingant_requests_get(url, retry=5)

    video_full_name = get_video_full_name(video_id, page_str)

    all_filenames = [file.name for file in pathlib.Path(output_dir).rglob('*.mp4')]
    if video_full_name + '.mp4' in all_filenames or video_id + '.mp4' in all_filenames:
        print(video_full_name + " 已经存在，跳过下载")
        return
    print("开始下载 %s " % video_full_name)

    result = re.search("https://.+m3u8", page_str)
    if not result:
        print("Get m3u8 url failed.")
        print(page_str)
        exit(1)
    m3u8url = result[0]

    m3u8url_list = m3u8url.split('/')
    m3u8url_list.pop(-1)
    download_url = '/'.join(m3u8url_list)
    m3u8file = os.path.join(output_dir, video_id + '.m3u8')

    response = utils.requests_with_retry(m3u8url)
    with open(m3u8file, 'wb') as f:
        f.write(response.content)

    m3u8obj = m3u8.load(m3u8file)
    m3u8uri = ''
    m3u8iv = ''
    os.remove(m3u8file)

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

    download_m3u8_video(ci, output_dir, ts_list, video_full_name)
    mv_video_and_download_cover(output_dir, video_id, video_full_name, page_str)


def scrape(ci, urls):
    try:
        ignore_proxy = CONF.get("save_vpn_traffic")
        response = utils.requests_with_retry(urls, retry=5, ignore_proxy=ignore_proxy)
    except Exception as e:
        print(e)
        return

    content_ts = response.content
    if ci:
        content_ts = ci.decrypt(content_ts)
    return content_ts

def download_m3u8_video(ci, output_dir, ts_list: list, video_full_name):
    buffer = io.BytesIO()
    tmp_video_filename = os.path.join(output_dir, video_full_name + ".tmp")
    target_video_filename = os.path.join(output_dir, video_full_name + ".mp4")
    log_filename = os.path.join(output_dir, video_full_name + ".log")

    last_ts = ''
    if os.path.exists(log_filename):
        with open(log_filename) as log_f:
            last_ts = log_f.readline()

    tmp_video_open_mode = 'wb'
    if last_ts in ts_list and os.path.exists(tmp_video_filename):
        index_start = ts_list.index(last_ts) + 1
        print('已经下载 %s 个文件, 开始断点续传...' % index_start)
        ts_list = ts_list[index_start:]
        tmp_video_open_mode = 'ab'
    
    download_list = ts_list
    start_time = time.time()
    print('开始下载 ' + str(len(download_list)) + ' 个文件..', end='')
    print('预计等待时间: {0:.2f} 分钟 视视频大小和网络速度而定)'.format(len(download_list) / 150))


    with open(tmp_video_filename, tmp_video_open_mode) as file, open(log_filename, 'w') as log_f:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
            results = executor.map(partial(scrape, ci), download_list)
            total_num = len(download_list)
            for i, result in enumerate(results):
                if not result:
                    print('error get content, skip')
                else:
                    print('\r当前下载: {0} , 剩余 {1} 个'.format(
                        i+1, total_num-i-1), end='', flush=True)

                    buffer.write(result)
                    # Adjust the buffer size as needed
                    if buffer.tell() >= BUFFER_SIZE:  # Example: 1MB buffer
                        buffer.seek(0)
                        file.write(buffer.read())
                        buffer.seek(0)
                        buffer.truncate()
                        log_f.write(download_list[i])
                        log_f.seek(0)

        # Write any remaining data in the buffer to the file
        buffer.seek(0)
        file.write(buffer.read())

    shutil.move(tmp_video_filename, target_video_filename)
    os.remove(log_filename)
    end_time = time.time()
    print('\n消耗 {0:.2f} 分钟 同步1个视频完成 !'.format((end_time - start_time) / 60))
