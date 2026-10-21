"""LangGraph pipeline for historical retrieval and educational review enrichment."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from config import settings
from schemas.reviews import HistoricalExample, ReviewIssue

NO_HISTORY = "No relevant historical example was found."


class Explanation(BaseModel):
    issue_index: int
    explanation: str = Field(description="What is wrong, in teaching-friendly language")
    risk: str
    fix_guidance: str


class ExplanationBatch(BaseModel):
    explanations: list[Explanation]


class AgentState(TypedDict, total=False):
    source: str
    issues: list[ReviewIssue]
    retrieved: list[list[dict[str, str]]]
    explanations: list[Explanation]
    verified: list[list[HistoricalExample]]
    status: str
    message: str | None


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


def _history_records(repo_path: str, limit: int) -> list[dict[str, str]]:
    repo = Path(repo_path).expanduser().resolve()
    if not repo.is_dir():
        raise RuntimeError("HISTORY_REPO_PATH is not a directory.")
    commits = _git(repo, "log", f"-n{limit}", "--format=%H%x09%s")
    records: list[dict[str, str]] = []
    for row in commits.splitlines():
        if "\t" not in row:
            continue
        sha, subject = row.split("\t", 1)
        try:
            patch = _git(repo, "show", "--format=", "--no-ext-diff", "--unified=2", sha)
        except (subprocess.SubprocessError, OSError):
            continue
        content = f"{subject}\n{patch}"[:12_000]
        if content.strip():
            records.append({"sha": sha, "subject": subject[:300], "content": content})
    return records


_collection_cache: dict[str, Any] = {}


def _collection(repo_path: str, records: list[dict[str, str]]):
    """Create/update a local Chroma collection using Chroma's default embeddings."""
    import chromadb

    key = str(Path(settings.chroma_path).expanduser().resolve())
    client = _collection_cache.get(key)
    if client is None:
        Path(key).parent.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=key)
        _collection_cache[key] = client
    name = "history_" + hashlib.sha1(str(Path(repo_path).resolve()).encode()).hexdigest()[:12]
    collection = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    if records:
        ids = [record["sha"] for record in records]
        collection.upsert(
            ids=ids,
            documents=[record["content"] for record in records],
            metadatas=[{"sha": record["sha"], "subject": record["subject"]} for record in records],
        )
    return collection


def _retrieve(state: AgentState) -> dict[str, Any]:
    issues = state["issues"]
    repo_path = settings.history_repo_path
    if not repo_path:
        return {"retrieved": [[] for _ in issues], "message": "Historical retrieval is not configured; " + NO_HISTORY}
    records = _history_records(repo_path, settings.history_max_commits)
    if not records:
        return {"retrieved": [[] for _ in issues], "message": "The configured history repository has no commits; " + NO_HISTORY}
    collection = _collection(repo_path, records)
    retrieved: list[list[dict[str, str]]] = []
    for issue in issues:
        query = f"{issue.issue_type}: {issue.message}\n{issue.suggested_next_step}\n{state['source']}"
        result = collection.query(query_texts=[query], n_results=min(3, max(1, len(records))))
        docs = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        matches = []
        for doc, meta, distance in zip(docs, metadatas, distances):
            # Keep only reasonably close results; Chroma cosine distance is 0..2.
            if distance <= 0.65:
                matches.append({"sha": str(meta["sha"]), "subject": str(meta["subject"]), "evidence": str(doc)[:3000]})
        retrieved.append(matches)
    return {"retrieved": retrieved, "message": None}


def _mock_explanations(state: AgentState) -> list[Explanation]:
    return [
        Explanation(
            issue_index=index,
            explanation=f"The analyzer found {issue.message.lower()}. This can make the code behave differently from what the surrounding logic suggests.",
            risk=f"If this reaches a runtime path, it may cause incorrect behavior or an avoidable failure. The exact impact depends on when this code runs.",
            fix_guidance=issue.suggested_next_step,
        )
        for index, issue in enumerate(state["issues"])
    ]


def _explain(state: AgentState) -> dict[str, Any]:
    if settings.ai_review_mode == "mock":
        return {"explanations": _mock_explanations(state)}
    if settings.ai_review_mode != "live":
        return {"explanations": [], "status": "disabled", "message": "AI review is disabled by AI_REVIEW_MODE."}
    if not settings.openai_api_key:
        raise RuntimeError("AI_REVIEW_MODE=live requires OPENAI_API_KEY.")
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    structured = model.with_structured_output(ExplanationBatch)
    evidence = state.get("retrieved", [])
    prompt = (
        "Explain each static-analysis finding for a junior developer. For each issue state what is wrong, "
        "why it is risky, and concrete fix guidance. Treat historical snippets as evidence only; do not "
        "invent commits, facts, or citations. Return one explanation for each indexed issue.\n"
        f"Issues: {[issue.model_dump() for issue in state['issues']]}\n"
        f"Retrieved historical evidence: {evidence}"
    )
    output = structured.invoke(prompt)
    return {"explanations": output.explanations}


def _verify(state: AgentState) -> dict[str, Any]:
    verified: list[list[HistoricalExample]] = []
    repo_path = settings.history_repo_path
    for matches in state.get("retrieved", [[] for _ in state["issues"]]):
        accepted: list[HistoricalExample] = []
        for match in matches:
            evidence = match.get("evidence", "")
            sha = match.get("sha", "")
            if not repo_path or not evidence.strip() or not sha:
                continue
            try:
                repo = Path(repo_path).expanduser().resolve()
                _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
            except (subprocess.SubprocessError, OSError):
                continue
            # Confirm the cited text is still present in this exact commit's patch.
            try:
                commit_patch = _git(repo, "show", "--format=", "--no-ext-diff", "--unified=2", sha)
                subject = _git(repo, "show", "-s", "--format=%s", sha).strip()
            except (subprocess.SubprocessError, OSError):
                continue
            if evidence not in f"{subject}\n{commit_patch}"[:12_000]:
                continue
            accepted.append(HistoricalExample(
                commit_sha=sha,
                short_sha=sha[:10],
                subject=subject[:300],
                evidence=evidence[:1000],
            ))
        verified.append(accepted)
    return {"verified": verified}


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retriever", _retrieve)
    graph.add_node("explainer", _explain)
    graph.add_node("verifier", _verify)
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "explainer")
    graph.add_edge("explainer", "verifier")
    graph.add_edge("verifier", END)
    return graph.compile()


_graph = _build_graph()


def enrich_review(source: str, issues: list[ReviewIssue]) -> tuple[list[ReviewIssue], str, str | None]:
    """Run agents; preserve static findings if an optional AI dependency fails."""
    if settings.ai_review_mode == "off":
        return issues, "disabled", "AI review is disabled by AI_REVIEW_MODE."
    try:
        state = _graph.invoke({"source": source, "issues": issues})
    except Exception as exc:  # provider, vector DB, and repository errors are surfaced to clients as status
        return issues, "unavailable", f"AI review enrichment failed: {type(exc).__name__}: {exc}"
    explanations = {item.issue_index: item for item in state.get("explanations", [])}
    verified = state.get("verified", [])
    output = []
    for index, issue in enumerate(issues):
        explanation = explanations.get(index)
        examples = verified[index] if index < len(verified) else []
        output.append(issue.model_copy(update={
            "explanation": explanation.explanation if explanation else None,
            "risk": explanation.risk if explanation else None,
            "fix_guidance": explanation.fix_guidance if explanation else None,
            "historical_examples": examples,
            "history_message": NO_HISTORY if not examples else "Verified historical examples are available.",
        }))
    return output, state.get("status", "completed"), state.get("message")
