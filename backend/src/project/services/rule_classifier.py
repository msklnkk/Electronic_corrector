import re
from typing import Dict, Optional


class RuleClassifier:
    def __init__(self) -> None:
        pass

    def classify(self, text: str, section: Optional[str] = None) -> Dict:
        text = text.strip()
        low = text.lower()


        if not text:
            return {"is_rule": False, "score": 0.0, "reason": "empty"}

        score = 0.0

        hard_noise_patterns = [
            "разработан центром",
            "утвержден на заседании",
            "введен взамен",
            "дата введения",
            "примеры библиографического описания",
            "подстрочные библиографические сноски",
            "рецензия на книгу",
            "электронные ресурсы",
            "книги и учебные пособия",
            "однотомные издания",
            "многотомные издания",
            "патентные документы",
            "авторефераты и диссертации",
        ]

        if any(p in low for p in hard_noise_patterns):
            return {"is_rule": False, "score": 0.05, "reason": "hard_noise"}

        if "url:" in low or "http://" in low or "https://" in low:
            return {"is_rule": False, "score": 0.0, "reason": "url"}

        modal_markers = [
            "должен",
            "должны",
            "следует",
            "не допускается",
            "допускается",
            "рекомендуется",
            "необходимо",
            "указывают",
            "помещают",
            "выполняют",
            "нумеруют",
            "обозначают",
            "приводят",
            "записывают",
            "печатают",
            "располагают",
            "отделяют",
            "проставляют",
            "включают",
            "начинают",
        ]
        if any(m in low for m in modal_markers):
            score += 0.55

        target_markers = [
            "шрифт",
            "текст работы",
            "страницы",
            "номер страницы",
            "заголовки",
            "таблицы",
            "рисунок",
            "иллюстрации",
            "ссылки",
            "сноски",
            "формулы",
            "приложения",
            "подразделы",
            "пункты",
            "подпункты",
            "источников",
            "заголовок",
            "поля",
        ]
        if any(t in low for t in target_markers):
            score += 0.2

        if re.search(r"\b(а4|а3|а2|а1|мм|см|пт|кегл|times new roman|полужирн|курсив|арабскими цифрами)\b", low):
            score += 0.15

        if section and section.startswith("6."):
            score += 0.15
        elif section and section.startswith("5."):
            score += 0.08

        if low.startswith("пример"):
            score -= 0.4

        if len(text.split()) < 3:
            score -= 0.4
        elif len(text.split()) < 5:
            score -= 0.2

        score = max(0.0, min(round(score, 2), 1.0))

        return {
            "is_rule": score >= 0.45,
            "score": score,
            "reason": "hybrid",
        }