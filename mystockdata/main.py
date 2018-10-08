'''
手工定期执行：  code_base_sync， 同步新股等数据
手工按需执行：  se_load_old_file， 同步 se 历史数据
执行： sync_all 同步其他数据，包括k线，市值等数据 
'''
import click

from mystockdata import se


@click.group()
def sync(chain=True):
    pass


def _se_sync():
    from mystockdata import se
    sh_pe = se.SSE()
    sh_pe.get_sse_overview_day()

    sz_se = se.SZSE()
    sz_se.get_szse_overview_day('sz')
    sz_se.get_szse_overview_day('szzb')
    sz_se.get_szse_overview_day('cyb')
    sz_se.get_szse_overview_day('zxqy')


@sync.command()
def se_sync():
    _se_sync()


def _code_base_sync():
    from mystockdata import code_base
    code_base.sync()


@sync.command()
def code_base_sync():

    _code_base_sync()


def _xdxr_sync(code=None, from_tdx=False):
    from mystockdata import xdxr, code_base
    if code:
        xdxr.download_code(code=code, from_tdx=from_tdx)
    else:
        code_list = code_base.stock_list()
        with click.progressbar(code_list) as bar:
            for code in bar:
                xdxr.download_code(code=code, from_tdx=from_tdx)


@sync.command()
@click.option('--code', default=None, help='Code')
@click.option('--from_tdx', default=False, help='是否强制从通达信获取')
def xdxr_sync(code=None, from_tdx=False):
    _xdxr_sync(code, from_tdx)


def _k_sync(code, force):
    from mystockdata import k, xdxr, code_base
    if code:
        k.sync_code(code=code, force=force)
    else:
        code_list = code_base.stock_list()
        with click.progressbar(code_list) as bar:
            for code in bar:
                k.sync_code(code=code, force=force)

        for code in ['999999', '399001', '399005', '399006']:
            k.sync_code(code=code, force=force)


@sync.command()
@click.option('--code', default=None, help='Code')
@click.option('--force',  is_flag=True, help='强制更新db数据')
def k_sync(code, force):
    _k_sync(code, force)


@sync.command()
def caculate():
    from mystockdata.market import caculate
    caculate()


@sync.command()
def show_marketdb():
    from mystockdata.market import MarketDb
    print(MarketDb.all().read()[['is_min', 'avg_close']])


@sync.command()
def sync_all():

    # _code_base_sync()
    print('同步交易所当天数据')
    _se_sync()
    print('同步k线数据')
    _k_sync(code=None, force=True)
    print('同步股份数据，用于计算市值')
    _xdxr_sync(code=None, from_tdx=None)


@click.group()
def se():
    pass


@se.command()
def se_load_old_file():
    if click.confirm('数据会刷新会2018-09-22，仍要执行吗？'):
        from mystockdata.se import load_old_file
        load_old_file()


@se.command()
def se_show():
    from mystockdata import se
    print(se.SE.get_pe())


@click.group()
def code():
    pass


@code.command()
@click.option('--code', help='Code')
def code_show(code):
    from mystockdata.code_base import CodeDb
    db = CodeDb(code=code)
    print(db.read())


# @click.group()
# def util():
#     pass


# @code.command()
# def sync_all():
#     pass
#     se_sync()
#     # xdxr_sync(None, False)
#     # k_sync(None, False)


cli = click.CommandCollection(sources=[se, code, sync])

if __name__ == '__main__':
    cli()
