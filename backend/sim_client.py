import asyncio
import json
import websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/events")as ws:
        print("Conectando... Aguarde eventos...")
        async for message in ws:
            print(json.loads(message))

asyncio.run(main())