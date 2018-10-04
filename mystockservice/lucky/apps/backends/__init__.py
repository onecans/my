from . import leveldb as backend


async def code_info(app, code, columns=None):
    rst = await backend.code_info(code, columns)
    return rst


async def code_list(app, where):
    return await backend.code_list(where)


async def loads_base_info(app, columns, codes=None):
    if columns == ['']:
        columns = None
    if codes == ['ALL']:
        codes = None
    return await backend.loads_base_info(columns, codes=codes)


async def se_info(app, column, category):
    return await backend.se_info(column, category)
