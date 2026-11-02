from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Protocol


class LLM(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class ReviewService:
    class LLMTimeoutError(Exception):
        pass

    class LLMUnavailableError(Exception):
        pass

    def __init__(self, llm: LLM, timeout: float = 10.0) -> None:
        self.llm = llm
        self.timeout = timeout

    def review(self, diff: str) -> dict[str, str]:
        prompt = f"Review this pull request and find problems:\n{diff}"
        # Execute synchronous LLM call with a timeout using a thread pool
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.llm.generate, prompt)
        try:
            answer = future.result(timeout=self.timeout)
        except FuturesTimeoutError:
            # Do not wait for the running task; ensure quick return
            executor.shutdown(wait=False, cancel_futures=True)
            raise ReviewService.LLMTimeoutError()
        except Exception:
            executor.shutdown(wait=False, cancel_futures=True)
            # Map any other exception to unavailable
            raise ReviewService.LLMUnavailableError()
        else:
            executor.shutdown(wait=False, cancel_futures=True)
            return {"comment": answer}
