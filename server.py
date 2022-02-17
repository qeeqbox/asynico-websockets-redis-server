from asyncio import get_event_loop, TimeoutError, sleep, gather
from websockets import client, serve
from aioredis import from_url
from contextlib import suppress

async def subscribers_task(websocket, channel):
	while True:
		message = await channel.get_message(ignore_subscribe_messages=True)
		if message is not None:
			if message["data"] == b"STOP":
				break
			await websocket.send(message['data'])
		await sleep(1)

async def websocket_handler(websocket):
	pub_redis = await from_url('redis://localhost:6379')
	pubsub = pub_redis.pubsub()
	await pubsub.subscribe("alerts")
	with suppress(Exception):
		await gather(subscribers_task(websocket, pubsub),)
	await pub_redis.close()

start_server = serve(websocket_handler, '0.0.0.0', 8001)
loop = get_event_loop()

try:
	loop.run_until_complete(start_server)
	loop.run_forever()
finally:
	loop.run_until_complete(loop.shutdown_asyncgens())
	loop.close()
