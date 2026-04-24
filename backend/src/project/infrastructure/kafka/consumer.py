import asyncio
import json
from aiokafka import AIOKafkaConsumer


TOPIC = "document-status-events"

# Если запускаешь consumer с Windows/локально:
BOOTSTRAP_SERVERS = "localhost:29092"

# Именно это имя потом появится в Kafka UI во вкладке Consumers
GROUP_ID = "document-status-consumer-group"


async def consume_document_statuses():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()
    print("Consumer запущен")
    print(f"Топик: {TOPIC}")
    print(f"Consumer group: {GROUP_ID}")
    print("Ожидаю статусы документов...\n")

    try:
        async for message in consumer:
            raw_value = message.value.decode("utf-8")

            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError:
                value = raw_value

            print("Получено сообщение из Kafka:")
            print(f"topic: {message.topic}")
            print(f"partition: {message.partition}")
            print(f"offset: {message.offset}")
            print(f"value: {value}")
            print("-" * 60)

    finally:
        await consumer.stop()
        print("Consumer остановлен")


if __name__ == "__main__":
    asyncio.run(consume_document_statuses())