import asyncio

import aiohttp
import aioredis
import async_timeout


async def fetch(session, url):
    async with async_timeout.timeout(100):
        async with session.get(url) as response:
            return await response.json()


async def get_codes():

    async with aiohttp.ClientSession() as session:
        codes = await fetch(session, 'http://127.0.0.1:9001/k/codes/SH')
        # html = await fetch(session, 'http://python.org')
        return codes


async def main():
    conn = aiohttp.TCPConnector(limit=50)

    codes = await get_codes()
    session = aiohttp.ClientSession(connector=conn)
    jobs = [fetch(session, 'http://127.0.0.1:9001/k/describe3/start/end?code=%s&col=volume&nocache' % code)
            for code in codes]
    rsts = []
    for next_ in asyncio.as_completed(jobs):
        r = await next_
        rsts.append(r)
    await session.close()


async def main2():
    conn = aiohttp.TCPConnector(limit=10)

    codes = await get_codes()
    session = aiohttp.ClientSession(connector=conn)
    jobs = [fetch(session, 'http://127.0.0.1:9001/k/describe/start/end?code=%s&col=volume&nocache' % ','.join(code))
            for code in chunk(codes, 100)]
    rsts = []
    for next_ in asyncio.as_completed(jobs):
        r = await next_
        rsts.append(r)
    await session.close()


def chunk(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]


if __name__ == '__main__':
    import time
    b = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    e = time.time()
    print(e-b)
