import json
from typing import Any

from project.core.llm_client import LLMClient


class LLMRuleEngine:
    def __init__(self):
        self.client = LLMClient()

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    async def evaluate_rule(self, rule: dict, ctx: dict) -> dict:
        section_hint = self._infer_section(rule)
        section_text = self._get_section_text(section_hint, ctx)
        full_text = ctx["text"]["full"][:20000]

        payload = {
            "rule": {
                "code": rule.get("rule_number") or rule.get("id"),
                "title": rule.get("title"),
                "description": rule.get("description"),
                "severity": rule.get("severity"),
                "check_type": rule.get("check_type"),
                "target": rule.get("target"),
                "operator": rule.get("operator"),
                "expected": rule.get("expected"),
                "options": rule.get("options", {}),
            },
            "document_context": {
                "available_sections": list(ctx["structure"].keys()),
                "section_hint": section_hint,
                "section_text": section_text[:12000] if section_text else "",
                "full_text_excerpt": full_text,
            },
        }

        system_prompt = """
Ты проверяешь документ по формальному правилу из стандарта.

Нужно ответить СТРОГО JSON-объектом вида:
{
  "status": "passed|failed|warning|manual_check|not_applicable",
  "problem": "строка",
  "evidence": "строка",
  "fix": "строка",
  "actual_value": null,
  "used_section": "строка или null"
}

Правила:
- passed: требование явно выполнено
- failed: требование явно нарушено
- warning: частично выполнено или есть сомнения
- manual_check: по имеющемуся тексту нельзя проверить надежно
- not_applicable: правило неприменимо к документу

Нельзя выдумывать факты.
Если данных недостаточно — manual_check.
Если раздел отсутствует и без него правило не проверить — not_applicable или failed, только если правило явно требует обязательный раздел.
Отвечай кратко и по делу.
"""

        user_prompt = json.dumps(payload, ensure_ascii=False)

        result = await self.client.json_completion(system_prompt, user_prompt)

        status = result.get("status", "manual_check")
        if status not in {"passed", "failed", "warning", "manual_check", "not_applicable"}:
            status = "manual_check"

        return {
            "status": status,
            "problem": str(result.get("problem") or ""),
            "evidence": str(result.get("evidence") or "LLM не дал объяснение."),
            "fix": str(result.get("fix") or ""),
            "actual_value": result.get("actual_value"),
            "used_section": result.get("used_section"),
        }

    def _infer_section(self, rule: dict) -> str | None:
        target = str(rule.get("target") or "")
        description = str(rule.get("description") or "").lower()

        if target.startswith("section:"):
            return target.split(":", 1)[1]

        if target.startswith("content:"):
            return target.split(":", 1)[1]

        if target.startswith("reference:"):
            return "references"

        if "введение" in description:
            return "introduction"
        if "заключение" in description:
            return "conclusion"
        if "содержание" in description or "оглавление" in description:
            return "content"
        if "приложен" in description:
            return "appendix"
        if "источник" in description or "литератур" in description or "библиограф" in description:
            return "references"
        if "сокращен" in description or "обозначен" in description:
            return "abbreviations"
        if "определени" in description:
            return "definitions"

        return None

    def _get_section_text(self, section: str | None, ctx: dict) -> str:
        if not section:
            return ""

        mapping = {
            "content": ctx["text"].get("content", ""),
            "introduction": ctx["text"].get("introduction", ""),
            "conclusion": ctx["text"].get("conclusion", ""),
            "references": ctx["text"].get("references", ""),
            "appendix": ctx["text"].get("appendix", ""),
            "definitions": ctx["text"].get("definitions", ""),
            "abbreviations": ctx["text"].get("abbreviations", ""),
        }
        return mapping.get(section, "")