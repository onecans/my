lucky Demo
==============

Example of mongo project using aiohttp_, motor_ and aiohttp_jinja2_,
similar to flask one. Here I assume you have *python3.5* and *docker* installed.

Installation
============

Clone repo and install library::

    $ git clone git@github.com:aio-libs/aiohttp-demos.git
    $ cd aiohttp-demos

Install the app::

    $ cd demos/lucky
    $ pip install -e .

Create database for your project::

    make docker_start_mongo
    make fake_data


Run application::

    $ make run

Open browser::

    http://127.0.0.1:9001


Requirements
============
* aiohttp_
* motor_
* aiohttp_jinja2_


.. _Python: https://www.python.org
.. _aiohttp: https://github.com/KeepSafe/aiohttp
.. _motor: https://github.com/mongodb/motor
.. _aiohttp_jinja2: https://github.com/aio-libs/aiohttp_jinja2


Cache:
    只缓存 Method 为GET的请求
    增加url query，带有nocache的不缓存

Usage:
    http://127.0.0.1:9001/k/describe/2018-01-01/2018-05-01/601600?where=INDEX&col=low
    http://127.0.0.1:9001/k/volume/2015-06-01/2018-09-01/601600?k=10
    http://127.0.0.1:9001/k/baseinfo/601600?col=totals,pe
    http://127.0.0.1:9001/k/codes/SH
    http://127.0.0.1:9001/k/line/2018-01-01/2018-05-01/601600
    http://127.0.0.1:9001/k/combin/2018-01-01/2018-05-01/601600?line&volume&describe&baseinfo 
    http://127.0.0.1:9001/k/line/2018-01-01/2018-09-01/399001

    http://127.0.0.1:9001/k/line/2007-01-01/2018-05-01/601600?nocache&col=shares
    http://127.0.0.1:9001/k/marketsize

    http://127.0.0.1:9001/k/min/2018-01-01/2018-09-01/601600?k=57
        - 相应期间内，近 k 天是否破新低


    http://127.0.0.1:9001/k/line2/2018-01-01/2018-05-01/601600?col=shares,high&nocache




Usage:
- 股票列表
    http://127.0.0.1:9001/se/codelist/SH?nocache
- 股票基本信息
    http://127.0.0.1:9001/baseinfo?nocache&col=pe,name
    http://127.0.0.1:9001/baseinfo/601600?nocache&col=pe,name

- 股票日线
    http://127.0.0.1:9001/code_info/start/end/601600?nocache

- 股票开始，结束两期间的涨幅，跌幅
    http://127.0.0.1:9001/k/range/2018-01-01/2018-01-30/601600?col=high&nocache

- 获取整个上市区间内，按照 resample 之后，破新高，破新低的股票， 破近期（window_size) 新高新低的股票数
    http://127.0.0.1:9001/k/max_counter/601600?nocache   
    http://127.0.0.1:9001/k/min_counter/601600?nocache 

- 最低点
    http://127.0.0.1:9001/k/min_k/2018-01-01/end/601600?nocache&k=50&col=volume


- pe
    http://127.0.0.1:9001/se/info?col=pe&category=SHA
    http://127.0.0.1:9001/se/info?col=pe&category=sh