import asyncio
import json

from sqlalchemy.exc import NoResultFound
import typer
from nats.aio.client import Client as NATS
from nats.js.api import ConsumerConfig, StreamConfig
from pydantic import BaseModel, TypeAdapter

from adaptors.mutators.orders import OrderMutator
from api.state import get_app_state

app = typer.Typer()
nats_client = NATS()


class PaidPayload(BaseModel):
    order_id: str


async def message_handler(msg):
    data = msg.data.decode()
    print(f"Received a message: {data}")
    adaptor = TypeAdapter(PaidPayload)
    payload = adaptor.validate_python(json.loads(data))
    try:
        await OrderMutator.mark_as_paid(get_app_state().pool, nats_client, payload.order_id)
    except NoResultFound:
        print("order not found")
    await msg.ack()



async def start_consumer(stream_name: str, subject: str):
    await nats_client.connect("nats://localhost:30042")
    js = nats_client.jetstream()

    try:
        await js.stream_info(stream_name)
    except Exception as e:
        if "not found" in str(e).lower():
            await js.add_stream(StreamConfig(name=stream_name, subjects=[subject]))
        else:
            return

    durable_name = "paid-event-consumer"

    try:
        # Try to get existing consumer info
        await js.consumer_info(stream_name, durable_name)
    except Exception as e:
        if "not found" in str(e).lower():
            # Create consumer if it doesn't exist
            consumer_config = ConsumerConfig(
                durable_name=durable_name, 
                ack_policy="explicit", 
                filter_subject=subject
            )
            await js.add_consumer(stream_name, consumer_config)

    # Create pull subscription using the consumer
    subscription = await js.pull_subscribe(subject, durable_name)
    print(f"Listening for messages on subject '{subject}' with consumer '{durable_name}'...")

    while True:
        try:
            messages = await subscription.fetch(batch=1, timeout=1)
            for message in messages:
                await message_handler(message)
                await message.ack()
        except Exception as e:
            if "timeout" not in str(e).lower():  # Ignore timeout exceptions
                print(f"Error processing messages: {e}")
        await asyncio.sleep(0.1)





@app.command()
def consume(stream_name: str = "events", subject: str = "events.paid"):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_consumer(stream_name, subject))


if __name__ == "__main__":
    app()
