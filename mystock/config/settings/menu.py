
SUIT_CONFIG = {
    'ADMIN_NAME': 'MyAdmin - Do Or Not Do, There is no Try!',
    'MENU_OPEN_FIRST_CHILD': True,
    'HEADER_DATE_FORMAT': 'Y-m-d',
    'HEADER_TIME_FORMAT': 'H:i:s O',
    'MENU': (

        # Keep original label and models
        # 'sites','auth',
        '-', '-', '-',

        {'label': 'PE', 'icon': 'icon-th-list', 'models': (
            {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/pe/SH'},
            {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/pe/SZ'},
            {'label': 'CYB', 'icon': 'icon-bookmark', 'url': '/datareader/pe/CYB'},
            {'label': 'ZXQY', 'icon': 'icon-bookmark', 'url': '/datareader/pe/ZXQY'}
        )},

        {'label': '流通市值', 'icon': 'icon-th-list', 'models': (
            {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/negotiable_val/SH'},
            {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/negotiable_val/SZ'},
            {'label': 'CYB', 'icon': 'icon-bookmark', 'url': '/datareader/negotiable_val/CYB'},
            {'label': 'ZXQY', 'icon': 'icon-bookmark', 'url': '/datareader/negotiable_val/ZXQY'}
        )},

        {'label': '市值', 'icon': 'icon-th-list', 'models': (
            {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/market_val/SH'},
            {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/market_val/SZ'},
            {'label': 'CYB', 'icon': 'icon-bookmark', 'url': '/datareader/market_val/CYB'},
            {'label': 'ZXQY', 'icon': 'icon-bookmark', 'url': '/datareader/market_val/ZXQY'}
        )},

        # {'label': '区间跌幅', 'icon': 'icon-th-list', 'models': (
        #     {'label': 'ALL', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331'},
        #     {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331?where=SH'},
        #     {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331?where=SZ'},
        # )},

        # {'label': '区间涨幅', 'icon': 'icon-th-list', 'models': (
        #     {'label': 'ALL', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331?'},
        #     {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331?where=SH'},
        #     {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/range/20180101/20180331?where=SZ'},
        # )},


        # {'label': '最高价位分布', 'icon': 'icon-th-list', 'models': (
        #     {'label': 'ALL', 'icon': 'icon-bookmark', 'url': '/datareader/max_date/20180101/20180331?'},
        #     {'label': 'SH', 'icon': 'icon-bookmark', 'url': '/datareader/max_date/20180101/20180331?where=SH'},
        #     {'label': 'SZ', 'icon': 'icon-bookmark', 'url': '/datareader/max_date/20180101/20180331?where=SZ'},
        # )},


    )
}
