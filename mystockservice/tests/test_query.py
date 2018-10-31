import asyncio

from lucky.apps.k.query import Line

l = Line(code='601600', where='SH')


loop = asyncio.get_event_loop()

df = loop.run_until_complete(l.to_df())

print(df)
