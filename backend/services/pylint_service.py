"""Run Pylint static analysis without executing submitted source code."""

import json
import re
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

from pylint.lint import Run

from schemas.reviews import ReviewIssue

_SEVERITY = {
    "fatal": "critical",
    "error": "high",
    "warning": "medium",
    "refactor": "low",
    "convention": "info",
    "info": "info",
}


def _next_step(message_id: str, symbol: str) -> str:
    if message_id == "E0602":
        return "Define the referenced name or correct the spelling before using it."
    if message_id == "C0114":
        return "Add a module-level docstring that describes this file's purpose."
    if message_id == "C0116":
        return "Add a concise docstring describing the function's behavior."
    if message_id == "W0611":
        return "Remove the unused import, or use it if it is required."
    if symbol == "line-too-long":
        return "Split the statement or wrap the expression to fit the configured line length."
    return f"Review this {symbol.replace('-', ' ')} finding and adjust the code to satisfy the reported rule."


def analyze_python(source: str, filename: str) -> list[ReviewIssue]:
    """Lint source from an isolated temporary file; never import or execute it."""
    try:
        with tempfile.TemporaryDirectory(prefix="second-pair-review-") as temp_dir:
            safe_name = Path(filename.replace("\\", "/")).name
            safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", safe_name)
            if not safe_name.endswith(".py"):
                safe_name = f"{safe_name}.py"
            source_path = Path(temp_dir) / safe_name
            source_path.write_text(source, encoding="utf-8")
            config_path = Path(temp_dir) / "pylintrc"
            config_path.write_text("", encoding="utf-8")
            capture = StringIO()
            # Explicit options avoid loading repository configuration or plugins.
            with redirect_stdout(capture):
                Run(
                    [
                        str(source_path),
                        "--output-format=json",
                        "--reports=n",
                        "--score=n",
                        "--persistent=n",
                        f"--rcfile={config_path}",
                    ],
                    exit=False,
                )
            output = capture.getvalue()
    except Exception as exc:
        raise RuntimeError("Static analysis could not be completed.") from exc

    try:
        records: list[dict[str, Any]] = json.loads(output or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Static analysis returned an invalid result.") from exc

    issues: list[ReviewIssue] = []
    for record in records:
        message_id = str(record.get("message-id", ""))
        symbol = str(record.get("symbol", "pylint"))
        category = str(record.get("type", "info")).lower()
        issues.append(
            ReviewIssue(
                issue_type=symbol,
                severity=_SEVERITY.get(category, "info"),
                line_number=record.get("line"),
                message=str(record.get("message", "Pylint reported an issue.")),
                suggested_next_step=_next_step(message_id, symbol),
            )
        )
    return issues
