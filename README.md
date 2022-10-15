# jable_downloader
download jable tv tool

![Scrutinizer code quality (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/quality/g/2niuhe/jable_downloader/main) ![GitHub top language](https://img.shields.io/github/languages/top/2niuhe/jable_downloader)
![Github_workflow](https://github.com/2niuhe/jable_downloader/actions/workflows/python-package.yml/badge.svg) ![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/2niuhe/jable_downloader)

![GitHub](https://img.shields.io/github/license/2niuhe/jable_downloader)
![Scrutinizer build (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/build/g/2niuhe/jable_downloader/main)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/2niuhe/jable_downloader)
![GitHub Repo stars](https://img.shields.io/github/stars/2niuhe/jable_downloader?style=social) 

### Introduction
下载jable tv视频助手:heart_eyes:

支持功能：
- **指定视频url下载到指定目录**
- **添加订阅某女星或者类别的视频，将该影星或类别的视频同步下载到本地**
- **支持断点续传，支持防止重复下载**
- **支持配置代理**
- 支持下载视频完毕后下载封面

### Usage

**使用方法**

```shell
# 安装依赖
pip install -r requirements.txt

# Linux设置代理(可选)
export https_proxy=http://127.0.0.1:7890 && export http_proxy=http://127.0.0.1:7890
# 配置文件中配置代理见Config小节(可选)

# 查看帮助
python main.py --help

# 指定视频url下载，指定多个url会按队列逐个下载(下面url替换为自己的url)
python main.py videos  https://jable.tv/videos/111111/  https://jable.tv/videos/222222/


# 添加对某类别的订阅，如添加`桜空もも`的订阅，添加订阅不会发起下载
python main.py subscription --add https://jable.tv/models/sakura-momo/

# 添加对多类别交集的订阅，如下添加`桜空もも的中文字幕`的订阅，添加订阅不会发起下载
python main.py subscription --add https://jable.tv/models/sakura-momo/ https://jable.tv/categories/chinese-subtitle/
# 查看当前订阅
python main.py subscription --get
# 下载/同步订阅内容到本地(不会下载已下载内容)
python main.py subscription --sync-videos


# h265编码压缩视频(可选)(体积可以减少超过一半)
ffmpeg -i input.mp4 -c:v libx265 -vtag hvc1 -c:a copy output.mkv
```

### Config(Optional)

配置项(json文件)说明

> 配置文件提供程序自定义选项，并记录一些订阅信息，配置文件可选
> 读取配置文件的路径是执行命令的工作路径，文件名为config.json

- downloadVideoCover： 是否下载封面,默认不下载
- downloadInterval： 每个视频之间的下载间隔，默认2s
- outputDir：下载的输出目录，默认当前工作目录
- proxies: 网络代理配置(需要同时配置http和https)
- subscriptions： 订阅的视频类别，支持models/tags等，建议通过命令行` python main.py subscription --add `添加
    - 添加订阅信息 `--add` 每次添加一个订阅，一个订阅`--add` 后添加多个url(url之间用空格分隔)表示是多个类型的交集
    - **订阅支持如下类型的url的任意组合**:
      - 女优:  https://jable.tv/models/sakura-momo/
      - 标签:  https://jable.tv/tags/flight-attendant/
      - 类型:  https://jable.tv/categories/chinese-subtitle/
      - 搜索:  https://jable.tv/search/天然美少女/
- videoIdBlockList: 需要跳过的番号列表，默认为空

*如下是订阅了桜空もも的中文字幕视频*

```json
{
    "downloadVideoCover": false,     
    "downloadInterval": 300,
    "outputDir": "./", 
    "proxies": {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890"
    },
    "videoIdBlockList": ["abc-123", "def-456"],
    "subscriptions": [
        [
            {
                "url": "https://jable.tv/models/sakura-momo/",
                "name": "桜空もも"
            },
            {
                "url": "https://jable.tv/categories/chinese-subtitle/",
                "name": "中文字幕"
            }
        ]
    ]
}
```

### Reference
[JableTVDownload](https://github.com/hcjohn463/JableTVDownload)
