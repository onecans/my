from mystockdata.db import CodeDb
from mystockdata.se import SE


def show_code(code):
    codedb = CodeDb(code=code)
    print(codedb.read())


def show_pe(code):
    print(SE.get_pe())
