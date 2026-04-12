# backend/src/project/infrastructure/kafka/publishers.py
from datetime import datetime

from project.infrastructure.kafka.config import (
    get_kafka_report_topic,
    get_kafka_status_topic,
)
from project.infrastructure.kafka.schemas import (
    DocumentStatusEvent,
    GenerateReportTask,
)


async def publish_status(kafka_producer, document_id: int, status: str, message: str, error: str | None = None):
    if kafka_producer is None:
        return

    event = DocumentStatusEvent(
        document_id=document_id,
        status=status,
        message=message,
        created_at=datetime.utcnow(),
        error=error,
    )

    await kafka_producer.send(
        get_kafka_status_topic(),
        event.model_dump(mode="json"),
    )


async def publish_report_task(kafka_producer, document_id: int, report_type: str = "json"):
    if kafka_producer is None:
        return

    task = GenerateReportTask(
        document_id=document_id,
        report_type=report_type,
        created_at=datetime.utcnow(),
    )

    await kafka_producer.send(
        get_kafka_report_topic(),
        task.model_dump(mode="json"),
    )