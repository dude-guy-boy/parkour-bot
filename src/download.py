import aiohttp, aiofiles

async def download(url, destination):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(destination, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                    return True
    except:
        return False