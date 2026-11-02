from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Protocol
import json

from app.redaction import redact_diff, extract_secret_values


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

    def review(self, diff: str) -> dict:
        # SEC-1: collect raw secret values and mask secrets before any LLM call
        raw_secret_values = extract_secret_values(diff)
        masked_diff, secrets_masked = redact_diff(diff)
        prompt = (
            "Return JSON with keys summary (string), risks (array), checks (array).\n"
            "Use evidence as either diff_line {type,file,line,proof} or rule {type,rule}.\n"
            f"Review this pull request and find problems:\n{masked_diff}"
        )
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

            def parse_answer(ans: str) -> tuple[str, list, list]:
                summary_local = None
                risks_local = []
                checks_local = []
                try:
                    data = json.loads(ans)
                    if isinstance(data, dict):
                        summary_local = str(data.get("summary") or "").strip()
                        risks_local = data.get("risks") or []
                        checks_local = data.get("checks") or []
                except Exception:
                    pass
                if not summary_local:
                    text = (ans or "").strip()
                    summary_local = "review summary unavailable" if not text else text[:300]
                    risks_local = []
                    checks_local = []
                return summary_local, risks_local, checks_local

            summary, risks, checks = parse_answer(answer)

            # Sanitize any leaked secret values in model output (D7)
            def sanitize_text(text: str) -> str:
                if not isinstance(text, str):
                    return text
                out = text
                for val in raw_secret_values:
                    if val:
                        out = out.replace(val, "[SECRET]")
                return out

            summary = sanitize_text(summary)
            checks = [sanitize_text(c) for c in (checks or []) if isinstance(c, str)]

            # Build index of masked diff: file -> new line number -> content
            def build_new_lines_index(masked: str) -> dict[str, dict[int, str]]:
                index: dict[str, dict[int, str]] = {}
                current_file: str | None = None
                new_line_no = 0
                for raw in masked.splitlines():
                    if raw.startswith("+++"):
                        # format: +++ b/path
                        parts = raw.split("\t")[0].split()
                        if len(parts) >= 2:
                            path = parts[1]
                            if path.startswith("b/"):
                                path = path[2:]
                            current_file = path
                            if current_file not in index:
                                index[current_file] = {}
                        continue
                    if raw.startswith("@@"):
                        # hunk header like: @@ -a,b +c,d @@
                        # extract c
                        try:
                            plus_part = raw.split("+")[1]
                            c_part = plus_part.split(",")[0]
                            c = int(c_part.strip().split()[0])
                        except Exception:
                            c = 0
                        new_line_no = c
                        continue
                    if current_file is None:
                        continue
                    if not raw:
                        continue
                    sign = raw[0]
                    content = raw[1:] if sign in {" ", "+", "-"} else raw
                    if sign == ' ' or sign == '+':
                        if new_line_no <= 0:
                            continue
                        index[current_file][new_line_no] = content
                        new_line_no += 1
                    elif sign == '-':
                        # deletion: new file line does not advance
                        continue
                return index

            index = build_new_lines_index(masked_diff)

            # QA-1 filtering using masked diff; cap to 3; order preserved (D6)
            filtered_risks: list[dict] = []
            allowed_rules = {"SEC-1", "API-1", "REL-1", "OUT-1", "SCOPE-1", "QA-1", "OBS-1"}
            for r in risks or []:
                if not isinstance(r, dict):
                    continue
                title = sanitize_text(r.get("title"))
                ev = r.get("evidence")
                if not title or not isinstance(ev, dict) or not ev.get("type"):
                    continue
                etype = ev.get("type")
                if etype == "rule" and ev.get("rule") in allowed_rules:
                    filtered_risks.append({"title": str(title), "evidence": {"type": "rule", "rule": ev.get("rule")}})
                elif etype == "diff_line":
                    file = ev.get("file")
                    line = ev.get("line")
                    proof = sanitize_text(ev.get("proof"))
                    if not (file and isinstance(line, int) and line >= 1 and proof):
                        pass
                    else:
                        # Verify file exists and line maps to content in masked diff (new version only)
                        if file in index and line in index[file]:
                            masked_line = index[file][line]
                            # Ensure proof is substring of masked line (D7)
                            if isinstance(proof, str) and proof in masked_line:
                                filtered_risks.append({
                                    "title": str(title),
                                    "evidence": {
                                        "type": "diff_line",
                                        "file": file,
                                        "line": line,
                                        "proof": proof,
                                    },
                                })
                if len(filtered_risks) >= 3:
                    break

            # Ensure checks is list of strings
            checks_list = []
            for c in checks or []:
                if isinstance(c, str):
                    checks_list.append(c)

            return {
                "summary": summary,
                "risks": filtered_risks,
                "checks": checks_list,
                "secrets_masked": int(secrets_masked),
            }
