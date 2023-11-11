import json
import os
from pathlib import Path
import re
import platform
import subprocess
import requests
import time
from urllib import parse

from config import CONF

video_index_cache_filename = "./jable_index_cache.json"

HEADERS = CONF.get("headers")

CHROMEDP_CMD = ""

logged = False


def get_video_ids_map_from_cache():
    cache = {}
    if os.path.exists(video_index_cache_filename):
        with open(video_index_cache_filename, 'r', encoding='utf-8') as f:
            cache = json.load(f)

    return cache


def _add_proxy(query_param):
    proxies_config = CONF.get('proxies', None)
    if proxies_config and 'http' in proxies_config and 'https' in proxies_config:
        query_param['proxies'] = proxies_config


def requests_with_retry(url, headers=HEADERS, timeout=20, retry=5):
    query_param = {
        'headers': headers,
        'timeout': timeout
    }
    _add_proxy(query_param)
    for i in range(1, retry+1):
        try:
            response = requests.get(url, **query_param)
        except Exception as e:
            if i == retry:
                print("Unexpected Error: %s" % e)
            time.sleep(120 * i)
            continue
        if str(response.status_code).startswith('2'):
            return response
        else:
            time.sleep(120 * i)
            continue
    raise Exception("%s exceed max retry time %s." % (url, retry))


def scrapingant_requests_get(url, retry=5) -> str:
    global logged
    if not CONF.get('sa_token'):
        if not logged:
            logged = True
            print("You need to go to https://app.scrapingant.com/ website to\n apply for a token and fill it in the sa_token field")
            print("Use local chromedp as a replacement.\n")
        return get_response_from_chromedp(url)
        exit(1)

    query_param = {
        "timeout": 180
    }

    sa_api = 'https://api.scrapingant.com/v2/general'
    qParams = {'url': url, 'x-api-key': CONF.get('sa_token'), 'browser': 'false'}
    if CONF.get('sa_mode', None) == 'browser':
        qParams['browser'] = 'true'
    reqUrl = f'{sa_api}?{parse.urlencode(qParams)}'

    proxies_config = CONF.get('proxies', None)

    if proxies_config and 'http' in proxies_config and 'https' in proxies_config:
        query_param['proxies'] = proxies_config

    for i in range(1, retry+1):
        try:
            response = requests.get(reqUrl, **query_param)
        except Exception as e:
            if i == retry:
                print("Unexpected Error: %s" % e)
            time.sleep(120 * i)
            continue

        if str(response.status_code).startswith('2'):
            return response.text
        else:
            time.sleep(120 * i)
            continue
    raise Exception("%s exceed max retry time %s" % (url, retry))


def update_video_ids_cache(data):
    with open(video_index_cache_filename, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


def get_local_video_list(path="./"):
    re_extractor = re.compile(r"[a-zA-Z0-9]{2,}-\d{3,}")

    def extract_movie_id(full_name):
        foo = re_extractor.search(full_name)
        movie_id = None
        if foo:
            movie_id = foo.group(0).lower()
        return movie_id

    result = {extract_movie_id(foo.name) for foo in list(Path(path).rglob("*.mp4"))}
    if None in result:
        result.remove(None)

    return result


def get_chromdp_binary_by_cpu_info():
    # 获取操作系统信息
    system = platform.system().lower()
    # 获取处理器架构信息
    arch = platform.machine().lower()
    short_arch = ""

    # 判断操作系统
    if system not in  ('linux', 'windows', 'darwin'):
        raise Exception('OS %s is not supported' % system)

    # 判断处理器架构
    if 'arm' in arch or 'aarch64' in arch:
        short_arch = 'arm64'
    elif 'x86' in arch or 'amd64' in arch:
        short_arch = 'x86_64'
    else:
        raise Exception('Arch %s is not supported' % arch)
    cmd = 'chromedp_jable_%s_%s' % (short_arch, system)
    cmd = cmd.lower()

    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, cmd)
    
    if not os.path.isfile(file_path):
        raise Exception("Canno find %s, you need download and put it in %s" % (cmd, current_dir))
    return cmd


def execute_command(command, timeout):
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output, error = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        output, error = process.communicate()
    
    return output.decode('utf-8')


def get_response_from_chromedp(url):
    global CHROMEDP_CMD
    if not CHROMEDP_CMD:
        CHROMEDP_CMD = get_chromdp_binary_by_cpu_info()

    cmd = "./%s %s" % (CHROMEDP_CMD, url)
    proxy = CONF.get('proxies', {}).get('http', None)

    if proxy:
        proxy_flag = " --proxy %s" % proxy
        cmd += proxy_flag
    
    return execute_command(cmd, 30)