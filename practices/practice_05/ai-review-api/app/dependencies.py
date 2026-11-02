"""Сборка зависимостей сервиса.

В учебном проекте настоящий LLM не подключён: StubLLM возвращает
фиксированный ответ без сетевых вызовов, чтобы тесты были быстрыми
и воспроизводимыми.
"""

from app.review_service import ReviewService


class StubLLM:
    def generate(self, prompt: str) -> str:
        return "stub review: no real LLM is connected"


review_service = ReviewService(llm=StubLLM(), timeout=10.0)
