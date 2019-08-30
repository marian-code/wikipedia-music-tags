import asyncio
import lyricsfinder

from aiohttp import ClientSession

async def main(query):
    async with ClientSession() as session:

        r = await lyricsfinder.search_lyrics(query, api_key="AIzaSyAlcmHItgtDPmCLqvqwKdmnceMXuBQHnuI", session=session).next()
        #print(r.title, r.artist, r.lyrics)

        #i = 0
        #async for r in lyrics_iterator:
        #    print(i)
        #    i += 1

        return r

loop = asyncio.get_event_loop()

tasks = asyncio.gather(*[main("We Accursed"), main("Golden Elk"), main("Brother Sister amorphis"), main("Honeyflow")])
done = loop.run_until_complete(tasks)

done = loop.run_until_complete(tasks)

#print(done.title, done.artist)
for fut in done:
    print(fut.title, fut.artist)
loop.close()

#result = asyncio.run(main())