# coding=utf-8
import codecs
import functools
import os.path
import time





def parse_code(code):
    try:
        _tmp = int(code)
        return str(_tmp).rjust(6, '0')
    except:
        # for 指数
        return code


def retry(tries=3, delay=5):
    def retry_(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mtries = tries
            while mtries > 0:
                mtries -= 1
                try:
                    rst = func(*args, **kwargs)
                    return rst
                except:
                    time.sleep(delay)

            return None

        return wrapper

    return retry_


def check_code_exists(file_name, code):
    rst = []
    try:
        with codecs.open(file_name, mode='rb', encoding='utf-8') as f:
            rst = f.readlines()
    except IOError as e:
        # 文件不存在
        if e.args[0] == 2:
            return False

    for line in rst:
        if line.find('"%s"' % parse_code(code)) >= 0:
            return True

    return False

