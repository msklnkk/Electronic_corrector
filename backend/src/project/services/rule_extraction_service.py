from typing import List
from project.schemas.bert_rules import ExtractedRule
from project.services.document_parser import parse_pdf_to_blocks
from project.services.rule_classifier import RuleClassifier
from project.services.rule_normalizer import (
    is_appendix_template,
    normalize_rule,
    split_into_atomic_rules,
)


class RuleExtractionService:
    def __init__(self) -> None:
        self.classifier = RuleClassifier()

    def deduplicate(self, rules: List[ExtractedRule]) -> List[ExtractedRule]:
        seen = set()
        result: List[ExtractedRule] = []

        for rule in rules:
            key = " ".join(rule.text.lower().split())
            if key in seen:
                continue
            seen.add(key)
            result.append(rule)

        return result

    def should_skip_by_context(self, rule: ExtractedRule) -> bool:
        text_l = rule.text.lower()

        if is_appendix_template(rule.text):
            return True

        if text_l.startswith("пример "):
            return True

        return False

    def extract_from_pdf(self, content: bytes) -> tuple[int, List[ExtractedRule]]:
        blocks = parse_pdf_to_blocks(content)
        rules: List[ExtractedRule] = []

        total_pages = max((block["page"] for block in blocks), default=0)

        for block in blocks:
            if is_appendix_template(block["text"]):
                continue

            atomic_rules = split_into_atomic_rules(block["text"])

            for item in atomic_rules:
                if is_appendix_template(item):
                    continue

                cls_item = self.classifier.classify(item, block["section"])

                if cls_item["score"] < 0.30:
                    continue

                rule = normalize_rule(
                    text=item,
                    section=block["section"],
                    page=block["page"],
                    confidence=cls_item["score"],
                )

                if self.should_skip_by_context(rule):
                    continue

                rules.append(rule)

        rules = self.deduplicate(rules)
        return total_pages, rules