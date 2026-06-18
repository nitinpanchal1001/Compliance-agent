"""Seed the policy corpus into Postgres + Qdrant.

Reads every *.md file under settings.policy_corpus_path, parses frontmatter and
`## ` clause headings, then:
  1. upserts a Policy row (global scope: tenant_id = NULL)
  2. chunks + embeds each clause
  3. upserts the vectors into the `policy_chunks` Qdrant collection

Idempotent: re-running updates the Policy row and overwrites the policy's points.

Run inside the api container (module form, so `core`/`db` are importable):
    docker compose exec api uv run python -m scripts.seed_policies
"""

import sys
from pathlib import Path

from sqlalchemy import select

from core import embeddings, vectorstore
from core.config import get_settings
from db.models.policy import Policy
from workers.chunking import chunk_text
from workers.db import get_sync_db

settings = get_settings()


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a leading `--- ... ---` block of key: value lines from the body."""
    meta: dict[str, str] = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def parse_clauses(body: str) -> list[tuple[str, str]]:
    """Split body on `## ` headings → list of (heading, clause_text)."""
    clauses: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                clauses.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)
    if current_heading is not None:
        clauses.append((current_heading, "\n".join(current_lines).strip()))
    return clauses


def split_section(heading: str) -> tuple[str, str]:
    """'Art. 5(1)(e) — Storage limitation' -> ('Art. 5(1)(e)', 'Storage limitation')."""
    if "—" in heading:
        section, _, label = heading.partition("—")
        return section.strip(), label.strip()
    return heading.strip(), heading.strip()


def seed_file(path: Path) -> int:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    regulation = meta.get("regulation") or path.stem.upper()
    title = meta.get("title", regulation)
    jurisdiction = meta.get("jurisdiction")
    source = meta.get("source")

    clauses = parse_clauses(body)
    if not clauses:
        print(f"  ! {path.name}: no clauses found, skipping")
        return 0

    # 1. Upsert the global Policy row.
    with get_sync_db() as db:
        existing = db.execute(
            select(Policy).where(
                Policy.tenant_id.is_(None), Policy.regulation == regulation
            )
        ).scalar_one_or_none()
        if existing:
            policy = existing
            policy.title = title
            policy.jurisdiction = jurisdiction
            policy.source = source
            policy.clause_count = len(clauses)
        else:
            policy = Policy(
                tenant_id=None,
                regulation=regulation,
                title=title,
                jurisdiction=jurisdiction,
                source=source,
                clause_count=len(clauses),
            )
            db.add(policy)
            db.flush()
        policy_id = policy.id

    # 2. Build chunks (clause may split into >1 chunk).
    chunk_records: list[dict] = []
    texts: list[str] = []
    for heading, clause_text in clauses:
        section, label = split_section(heading)
        citation = f"{regulation} {section} — {label}" if label else f"{regulation} {section}"
        # section is unique within a regulation, so the clause-local index is
        # enough to make each point ID unique.
        for idx, piece in enumerate(chunk_text(clause_text)):
            chunk_records.append(
                {
                    "policy_id": policy_id,
                    "owner": "global",
                    "regulation": regulation,
                    "section": section,
                    "citation": citation,
                    "chunk_index": idx,
                    "text": piece,
                }
            )
            texts.append(piece)

    # 3. Embed all pieces in one batch, attach vectors, upsert.
    vectors = embeddings.embed_texts(texts)
    for record, vector in zip(chunk_records, vectors):
        record["vector"] = vector

    vectorstore.ensure_policy_collection()
    vectorstore.delete_policy(policy_id)
    vectorstore.upsert_policy_chunks(chunk_records)

    print(f"  ✓ {regulation}: {len(clauses)} clauses → {len(chunk_records)} chunks")
    return len(chunk_records)


def main() -> None:
    corpus = Path(settings.policy_corpus_path)
    if not corpus.exists():
        print(f"Corpus path not found: {corpus}", file=sys.stderr)
        sys.exit(1)

    files = sorted(corpus.glob("*.md"))
    if not files:
        print(f"No .md files in {corpus}", file=sys.stderr)
        sys.exit(1)

    print(f"Seeding {len(files)} policy file(s) from {corpus}")
    total = 0
    for path in files:
        total += seed_file(path)
    print(f"Done. {total} policy chunks embedded into '{settings.policy_collection}'.")


if __name__ == "__main__":
    main()
