import json
import os


CONF = {
    "downloadVideoCover": False,
    "downloadInterval": 0,
    "outputDir": "./",
    "outputFileFormat": 'title.mp4',
    "proxies": {},
    "save_vpn_traffic": False,
    "subscriptions": [],
    "videoIdBlockList": [],
    "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0"
    }
}


def get_config(conf_path='./config.json'):
    if not os.path.exists(conf_path):
        return

    with open(conf_path, 'r', encoding='utf8') as f:
        return CONF.update(json.load(f))


def update_config(conf, conf_path='./config.json'):
    with open(conf_path, 'w', encoding='utf8') as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)


get_config()

headers = CONF.get("headers")
