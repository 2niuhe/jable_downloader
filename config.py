import json
import os


def get_config(conf_path='./config.json'):
    if not os.path.exists(conf_path):
        return {}

    with open(conf_path, 'r', encoding='utf8') as f:
        return json.load(f)


def update_config(conf, conf_path='./config.json'):
    with open(conf_path, 'w', encoding='utf8') as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)


CONF = get_config()
default_headers = "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0"
headers = CONF.get("headers", default_headers)
