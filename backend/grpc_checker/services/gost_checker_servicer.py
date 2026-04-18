# backend/grpc_checker/services/gost_checker_servicer.py
import json
import time
from enum import Enum

import grpc
import asyncio

# Сгенерированные protobuf файлы
from grpc_checker.generated import gost_checker_pb2_grpc, gost_checker_pb2

from project.gost_checker.checker import GOSTDocumentChecker


class SafeEncoder(json.JSONEncoder):
    # Кастомный JSON энкодер для нестандартных типов
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

class GostCheckerServicer(gost_checker_pb2_grpc.GostCheckerServiceServicer):

    def __init__(self):
        self._checker_cache: dict[str, GOSTDocumentChecker] = {}
        print("gRPC GostCheckerServicer инициализирован")

    def _resolve_rules_path(self, request) -> str:
        meta = dict(request.metadata) if request.metadata else {}
        if meta.get("rules_file"):
            return meta["rules_file"]
        if request.gost_versions:
            return request.gost_versions[0]
        raise ValueError("Не выбран ГОСТ: путь к файлу правил не передан в gRPC metadata.rules_file")

    def _get_checker(self, rules_path: str) -> GOSTDocumentChecker:
        if rules_path not in self._checker_cache:
            self._checker_cache[rules_path] = GOSTDocumentChecker(rules_file=rules_path)
        return self._checker_cache[rules_path]

    async def CheckDocument(self, request, context):
        # Основной метод проверки документа через gRPC
        start_time = time.time()

        try:
            rules_path = self._resolve_rules_path(request)
            checker = self._get_checker(rules_path)
            # Вызываем чекер с байтами
            report = await checker.check_document(
                file_content=request.file_content,
                filename=request.file_name,
                document_id=request.document_id or "unknown",
                original_filename=request.file_name
            )

            # Преобразуем ошибки в protobuf
            mistakes = []
            for result in report.get_failed_results():
                mistakes.append(gost_checker_pb2.Mistake(
                    code=result.rule_id,
                    description=result.message,
                    location="",  # можно добавить позже (страница, параграф и т.д.)
                    severity=result.severity.value,
                    gost_reference=result.section
                ))

            processing_time_ms = int((time.time() - start_time) * 1000)

            passed = report.passed_checks
            total = report.total_checks or 1
            score = int(round((passed / total) * 100)) if total > 0 else 0

            status = "compliant" if passed == total else "has_errors"

            summary = json.dumps(report.to_dict(), cls=SafeEncoder, ensure_ascii=False)

            return gost_checker_pb2.CheckDocumentResponse(
                success=True,
                mistakes=mistakes,
                summary_report=summary,  # можно отправлять весь отчет
                processing_time_ms=processing_time_ms,
                status=status
            )

        except Exception as e:
            print(f"Ошибка в gRPC CheckDocument: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Ошибка проверки документа: {str(e)}")

            return gost_checker_pb2.CheckDocumentResponse(
                success=False,
                mistakes=[],
                summary_report=json.dumps({"error": str(e)}, ensure_ascii=False),
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="error"
            )


# Функция запуска сервера
async def serve_grpc():
    server = grpc.aio.server()
    gost_checker_pb2_grpc.add_GostCheckerServiceServicer_to_server(
        GostCheckerServicer(), server
    )

    server.add_insecure_port('[::]:50051')
    await server.start()
    print("gRPC Checker Service запущен на порту 50051")
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve_grpc())