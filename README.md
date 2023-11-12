# jable_downloader
download jable tv tool

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)
![Scrutinizer code quality (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/quality/g/2niuhe/jable_downloader/main)
![Github_workflow](https://github.com/2niuhe/jable_downloader/actions/workflows/python-package.yml/badge.svg)
![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/2niuhe/jable_downloader)

![GitHub top language](https://img.shields.io/github/languages/top/2niuhe/jable_downloader)
![GitHub](https://img.shields.io/github/license/2niuhe/jable_downloader)
![Scrutinizer build (GitHub/Bitbucket)](https://img.shields.io/scrutinizer/build/g/2niuhe/jable_downloader/main)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/2niuhe/jable_downloader)
![GitHub Repo stars](https://img.shields.io/github/stars/2niuhe/jable_downloader?style=social)
![Github All Releases](https://img.shields.io/github/downloads/2niuhe/jable_downloader/total.svg)

### Introduction
下载jable tv视频助手:heart_eyes:

> **旧版支持订阅等其他功能的在archive分支或者从release下载**
> [旧版分支](https://github.com/2niuhe/jable_downloader/tree/archive)
> [v1.2.1旧版release](https://github.com/2niuhe/jable_downloader/releases/tag/v1.2.1)

支持功能：
- **指定视频url下载到指定目录**
- **支持断点续传，支持防止重复下载**
- **支持配置代理**
- **支持url列表**
  - m3u8类型
  - jable
  - missav(TODO)

### Usage

**使用方法**
需要从release中下载对应系统和cpu架构的chromedp_jable文件，放到main.py同级目录，需要电脑安装有chrome浏览器



```shell
# 安装依赖
pip install -r requirements.txt

# 配置网络代理见Config小节(可选)

# 查看帮助
python main.py --help

# 指定视频url下载，指定多个url会按队列逐个下载(下面url替换为自己的url)
python main.py  https://jable.tv/videos/111111/  https://jable.tv/videos/222222/



# h265编码压缩视频(可选)(体积可以减少为原1/3，实测1.8G的视频可以压缩到500M，耗时30分钟)
ffmpeg -i input.mp4 -c:v libx265 -vtag hvc1 -c:a copy output.mkv
```

**使用帮助**

1. **下载完视频无法播放或者卡帧**
    - 解决方案1： 更换视频播放器，推荐[mpv播放器](https://mpv.io/installation/)
    - 解决方案2： 使用ffmpeg编码`ffmpeg -i input.mp4 -c:v libx264 -vtag hvc1 -c:a copy output.mp4`

### Config(Optional)

配置项(json文件)说明

> 配置文件提供程序自定义选项，配置文件可选
> 读取配置文件的路径是执行命令的工作路径，文件名为config.json

- outputDir：下载的输出目录，默认当前工作目录
- outputFileFormat: 下载文件的格式，默认是"title.mp4"，即视频标题作为文件名，可选配置如下:
    - "title.mp4": 默认值，即视频标题作为文件名 (**推荐**)
    - "id.mp4": 番号作为文件名
    - "id/title.mp4": 番号目录/视频标题.mp4 (创建子目录，番号作为子目录名，标题作为文件名) 
    - "id/id.mp4": 番号目录/番号.mp4 （创建子目录，番号作为子目录名，番号作为文件名)
- proxies: 网络代理配置(需要同时配置http和https)
- headers: 自定义请求头，一般不需要改动

*如下是配置了代理的示例*

```json
{
    "outputDir": "./",
    "outputFileFormat": "",  
    "proxies": {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890"
    },
    "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
    }
}
```

### Reference
[JableTVDownload](https://github.com/hcjohn463/JableTVDownload)
