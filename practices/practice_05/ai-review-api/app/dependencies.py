"""Сборка зависимостей сервиса.

В учебном проекте настоящий LLM не подключён: StubLLM возвращает
фиксированный ответ без сетевых вызовов, чтобы тесты были быстрыми
и воспроизводимыми.
"""

import json

from app.review_service import ReviewService


class StubLLM:
    """Детерминированная заглушка: JSON по specs/review-api-contract.md (R5).

    Видит только промпт с уже замаскированным diff (SEC-1), поэтому о секретах
    знает лишь по маркеру [SECRET]; риски подтверждает правилами (QA-1).
    """

    def generate(self, prompt: str) -> str:
        risks = []
        if "[SECRET]" in prompt:
            risks.append({
                "title": "В diff найдены секреты: уберите их из кода и перевыпустите ключи",
                "evidence": {"type": "rule", "rule": "SEC-1"},
            })
        return json.dumps({
            "summary": "Учебная заглушка LLM: настоящая модель не подключена, отзыв сформирован по правилам проекта.",
            "risks": risks,
            "checks": [
                "Запустите проверки проекта: sh scripts/check.sh",
                "Проверьте граничные случаи изменённого кода",
            ],
        }, ensure_ascii=False)


review_service = ReviewService(llm=StubLLM(), timeout=10.0)
