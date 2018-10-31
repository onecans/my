import os
from django.conf import settings

# 是否仅仅使用CACHE
ONLY_CACHE = settings.TSLIB_ONLY_CACHE if getattr(settings,'TSLIB_ONLY_CACHE') else True


CACHE_DIR = settings.TSLIB_CACHE_DIR if getattr(settings, 'TSLIB_CACHE_DIR') else '/tmp/s'

try:
    os.mkdir(CACHE_DIR)
except OSError as e:
    if e.args[0] == 17:  # (17, 'File exists')
        pass
    else:
        raise
