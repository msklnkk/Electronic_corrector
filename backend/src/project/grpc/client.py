# backend/src/project/grpc/client.py
import grpc
from typing import Optional
import sys
sys.path.insert(0, '/app')

from grpc_checker.generated import gost_checker_pb2_grpc, gost_checker_pb2


class GostCheckerClient:
    # gRPC клиент для вызова сервиса проверки документов

    def __init__(self, target: str = "grpc_checker:50051"):
        self.target = target
        self.channel = None
        self.stub = None

    async def connect(self):
        # Создает соединение (ленивая инициализация)
        if self.channel is None:
            self.channel = grpc.aio.insecure_channel(self.target)
            self.stub = gost_checker_pb2_grpc.GostCheckerServiceStub(self.channel)
            print(f"gRPC клиент подключен к {self.target}")

    async def check_document(
        self,
        file_content: bytes,
        file_name: str,
        document_id: Optional[str] = None
    ) -> gost_checker_pb2.CheckDocumentResponse:
        # Отправляет документ на проверку через gRPC
        await self.connect()

        request = gost_checker_pb2.CheckDocumentRequest(
            document_id=document_id or "unknown",
            file_content=file_content,
            file_name=file_name
        )

        # Таймаут 60 секунд
        response = await self.stub.CheckDocument(request, timeout=60.0)
        return response

    async def close(self):
        # Закрывает соединение
        if self.channel:
            await self.channel.close()
            self.channel = None
            self.stub = None