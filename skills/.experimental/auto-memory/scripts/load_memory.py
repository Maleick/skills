#!/usr/bin/env python3
"""Retrieve project-scoped memory notes with hybrid ranking."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import urllib.error
import urllib.request

from common import (
    MemoryValidationError,
    ensure_project_name,
    list_notes,
    memory_dir_for_project,
)

EMBEDDING_MODEL = "text-embedding-3-small"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load project memory notes via keyword + embedding search.")
    parser.add_argument("--project", required=True, help="Project scope for memory operations.")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum results to return (default: 8).")
    return parser.parse_args()


def tokenize_query(query: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9][a-z0-9_-]*", query.lower()) if len(token) > 1]


def keyword_score(note, query: str, tokens: list[str]) -> float:
    title = note.title.lower()
    tags_text = " ".join(note.tags).lower()
    headings_text = " ".join(re.findall(r"^##\s+(.+)$", note.body, re.MULTILINE)).lower()
    body = note.body.lower()
    query_lower = query.lower()

    score = 0.0
    if query_lower and query_lower in title:
        score += 12.0
    if query_lower and query_lower in body:
        score += 4.0

    for token in tokens:
        score += min(title.count(token), 3) * 4.0
        score += min(tags_text.count(token), 3) * 3.0
        score += min(headings_text.count(token), 5) * 2.0
        score += min(body.count(token), 20) * 0.5
    return score


def build_highlights(note, tokens: list[str], max_items: int = 3) -> list[str]:
    highlights: list[str] = []
    lines = [line.strip() for line in note.body.splitlines() if line.strip() and not line.startswith("## ")]

    for line in lines:
        lowered = line.lower()
        if any(token in lowered for token in tokens):
            clipped = line if len(line) <= 180 else f"{line[:177]}..."
            if clipped not in highlights:
                highlights.append(clipped)
        if len(highlights) >= max_items:
            return highlights

    for line in lines:
        clipped = line if len(line) <= 180 else f"{line[:177]}..."
        if clipped not in highlights:
            highlights.append(clipped)
        if len(highlights) >= max_items:
            break
    return highlights


def should_try_embedding_fallback(sorted_keyword_scores: list[tuple], limit: int) -> bool:
    if not sorted_keyword_scores:
        return True
    top_score = sorted_keyword_scores[0][1]
    min_results = min(limit, 3)
    return top_score < 8.0 or len(sorted_keyword_scores) < min_results


def embedding_payload(query: str, notes: list) -> list[str]:
    payload: list[str] = [query]
    for note in notes:
        text = (
            f"title: {note.title}\n"
            f"tags: {', '.join(note.tags)}\n"
            f"date: {note.date}\n"
            f"body:\n{note.body}"
        )
        payload.append(text[:6000])
    return payload


def fetch_embeddings(inputs: list[str], api_key: str) -> list[list[float]]:
    url = "https://api.openai.com/v1/embeddings"
    payload = {"model": EMBEDDING_MODEL, "input": inputs}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Embedding API request failed: HTTP {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Embedding API request failed: {exc.reason}") from exc

    parsed = json.loads(raw.decode("utf-8"))
    data_rows = parsed.get("data", [])
    vectors = [row.get("embedding") for row in data_rows]
    if len(vectors) != len(inputs):
        raise RuntimeError("Embedding API response shape mismatch.")
    return vectors


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def rank_with_embeddings(notes: list, lexical_scores: dict[str, float], query: str, limit: int) -> list[tuple]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    inputs = embedding_payload(query, notes)
    vectors = fetch_embeddings(inputs, api_key=api_key)
    query_vector = vectors[0]
    note_vectors = vectors[1:]

    lexical_top = max(lexical_scores.values()) if lexical_scores else 0.0
    ranked: list[tuple] = []
    for note, vector in zip(notes, note_vectors):
        semantic_score = cosine_similarity(query_vector, vector)
        lexical_raw = lexical_scores.get(str(note.path), 0.0)
        lexical_norm = lexical_raw / lexical_top if lexical_top > 0 else 0.0
        final_score = (0.6 * semantic_score) + (0.4 * lexical_norm)
        ranked.append((note, final_score))
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked[:limit]


def format_result(note, score: float, match_type: str, query_tokens: list[str]) -> dict:
    return {
        "filename": note.path.name,
        "title": note.title,
        "date": note.date,
        "tags": note.tags,
        "highlights": build_highlights(note, query_tokens),
        "score": round(score, 6),
        "match_type": match_type,
    }


def main() -> int:
    args = parse_args()
    try:
        project = ensure_project_name(args.project)
    except MemoryValidationError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 2

    query = args.query.strip()
    limit = max(1, args.limit)
    project_dir = memory_dir_for_project(project)
    notes = [note for note in list_notes(project_dir) if not note.frontmatter.get("superseded_by")]

    if not query:
        print(json.dumps({"status": "error", "error": "query must not be empty"}, indent=2))
        return 2

    if not notes:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "project": project,
                    "query": query,
                    "limit": limit,
                    "results": [],
                    "message": "No matching memory entries found.",
                },
                indent=2,
            )
        )
        return 0

    query_tokens = tokenize_query(query)
    scored = [(note, keyword_score(note, query, query_tokens)) for note in notes]
    scored = [item for item in scored if item[1] > 0.0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    lexical_scores = {str(note.path): score for note, score in scored}
    weak_keywords = should_try_embedding_fallback(scored, limit)
    embedding_fallback_skipped = None
    retrieval_mode = "keyword"

    if weak_keywords:
        try:
            candidate_notes = notes
            embedding_ranked = rank_with_embeddings(candidate_notes, lexical_scores, query, limit)
            final = [format_result(note, score, "embedding", query_tokens) for note, score in embedding_ranked]
            retrieval_mode = "embedding"
        except Exception as exc:
            embedding_fallback_skipped = str(exc)
            final = [format_result(note, score, "keyword", query_tokens) for note, score in scored[:limit]]
    else:
        final = [format_result(note, score, "keyword", query_tokens) for note, score in scored[:limit]]

    message = None
    if not final:
        message = "No matching memory entries found."

    print(
        json.dumps(
            {
                "status": "ok",
                "project": project,
                "query": query,
                "limit": limit,
                "retrieval_mode": retrieval_mode,
                "embedding_fallback_skipped": embedding_fallback_skipped,
                "results": final,
                "message": message,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

