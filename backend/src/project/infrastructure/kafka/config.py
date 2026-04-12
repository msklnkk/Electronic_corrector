import os


def get_kafka_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def get_kafka_status_topic() -> str:
    return os.getenv("KAFKA_STATUS_TOPIC", "document-status-events")


def get_kafka_report_topic() -> str:
    return os.getenv("KAFKA_REPORT_TOPIC", "generate-report-task")


def get_kafka_group_id() -> str:
    return os.getenv("KAFKA_GROUP_ID", "report-worker-group")