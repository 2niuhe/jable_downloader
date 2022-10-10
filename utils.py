import os
import re
import time
from pathlib import Path


def get_local_video_list(path="./"):
    re_extractor = re.compile(r"[a-zA-Z0-9]{3,}-\d{3,}")

    def extract_movie_id(full_name):
        foo = re_extractor.search(full_name)
        movie_id = None
        if foo:
            movie_id = foo.group(0).lower()
        return movie_id

    result = {extract_movie_id(str(foo)) for foo in list(Path(path).rglob("*.mp4"))}
    if None in result:
        result.remove(None)

    return result


def merge_mp4(input_path, output_path, video_name, tsList):
    start_time = time.time()
    print('开始合成视频...')

    for i in range(len(tsList)):
        file = tsList[i].split('/')[-1][0:-3] + '.mp4'
        full_path = os.path.join(input_path, file)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f1:
                with open(os.path.join(output_path, video_name + '.mp4'), 'ab') as f2:
                    f2.write(f1.read())
        else:
            # TODO: retry download
            print(file + "不存在 失败 ")
    end_time = time.time()
    print('消耗 {0:.2f} 秒合成视频'.format(end_time - start_time))
    print('%s 下载完成!' % video_name)


def deleteM3u8(folderPath):
    files = os.listdir(folderPath)
    for file in files:
        if file.endswith('.m3u8'):
            os.remove(os.path.join(folderPath, file))
