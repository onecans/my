import copy
import os

from fabric.api import *

from myfab import aiohttp, python

PRODUCTION = '10.16.27.213'

RUNING_USER = 'nobody'
GIT_URL = 'git@10.138.94.96:itdev01/lucky.git'
GIT_BRANCH = 'master'
GIT_BASE_ROOT = '/u01'
AIOHTTP_APP = 'lucky.main:gunicorn_app'
AIOHTTP_CONF_FILE = 'config/config.yml'
AIOHTTP_CONF_PROD_FILE = 'config/config_prod.yml'
IS_INSTALL_MYSQL = False
IS_UPLOAD_PROD_SETTINGS = True
GUNICORN_BIND = '0.0.0.0:9001'

_tmp = copy.copy(locals())
config = {}
for k, v in _tmp.items():
    if k == k.upper():
        config[k] = v


@hosts(PRODUCTION)
def install_python3():
    python.install3_6()


@hosts(PRODUCTION)
def ci():
    aiohttp.ci(config)


@hosts(PRODUCTION)
def restart():
    aiohttp.restart(config)


@hosts(PRODUCTION)
def ci_and_restart():
    ci()
    restart()
