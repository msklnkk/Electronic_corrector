import json

from aiokafka import AIOKafkaProducer


class KafkaProducerService:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda value: json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            ).encode("utf-8"),
        )
        await self.producer.start()

    async def stop(self) -> None:
        if self.producer is not None:
            await self.producer.stop()

    async def send(self, topic: str, payload: dict) -> None:
        if self.producer is None:
            raise RuntimeError("Kafka producer is not started")
        await self.producer.send_and_wait(topic, payload)