# Regulation Ingestion Plan

How the compliance corpus (GDPR, HIPAA, PCI-DSS, RBI, SEBI, SOX) is built, and the
plan to ingest each regulation in its official form.

## Decisions (locked)

- **Fidelity: hybrid.** Verbatim official text where it is public and machine-readable
  (GDPR, HIPAA, SOX); faithful, well-cited structured clauses for the rest (RBI, SEBI),
  and a faithful paraphrase for PCI-DSS (copyright — see below).
- **RBI / SEBI scope: default set** (these are libraries of many circulars, not single
  documents, so we scope to the compliance-relevant ones):
  - **RBI:** Digital Payment Security Controls; Cyber Security Framework; KYC Master
    Direction; IT Governance / Outsourcing of IT Services.
  - **SEBI:** LODR; Prohibition of Insider Trading (PIT); Cyber Security & Cyber
    Resilience framework.
- **PCI-DSS: faithful paraphrase.** PCI DSS v4.0.1 is © PCI SSC and cannot be
  redistributed verbatim. We ingest our own paraphrase of the 12 requirements and key
  sub-requirements, keyed to the official requirement numbers. (Alternative if needed:
  ingest a licensed copy locally, uncommitted.)

## Current state

- Corpus lives in `policy_corpus/`, mounted read-only to `/policy_corpus` in the api and
  worker containers (`docker-compose.yml`).
- Files present: `gdpr.md`, `hipaa.md`, `sox.md`, `pci_dss.md` — now **expanded** to a
  realistic clause count (see "Interim expansion" below). `rbi/` and `sebi/` are empty
  placeholders pending Phase B.
- Format: frontmatter (`regulation`, `title`, `jurisdiction`, `source`) + `## Section —
  Label` clause headings. `scripts/seed_policies.py` parses → chunks (1000/150) → embeds
  (OpenAI `text-embedding-3-small`, 1536-d) → upserts to Qdrant `policy_chunks` as global
  (`tenant_id = NULL`), idempotently. Clause text currently lives only in Qdrant; the
  Postgres `Policy` row holds aggregate metadata + `clause_count`.

## Interim expansion (done now, no fetch cost)

Pending the full fetch pipeline, the four existing bodies (GDPR, HIPAA, SOX, PCI-DSS)
have been expanded from ~8–10 clauses each to a comprehensive, faithful set with exact
citations, authored as structured clauses (not fetched). Re-run `make seed-policies` to
embed them. This is illustrative-but-faithful; the Phase A fetch (below) will replace the
verbatim-eligible ones (GDPR/HIPAA/SOX) with official text.

## Source availability

| Source   | Official, machine-readable?                          | Volume                                  | Catch |
|----------|------------------------------------------------------|-----------------------------------------|-------|
| GDPR     | Yes — EUR-Lex, Reg (EU) 2016/679 (XML/HTML)          | 99 Articles (+173 Recitals)             | Public |
| HIPAA    | Yes — eCFR 45 CFR Parts 160/162/164 (API)            | Privacy/Security/Breach rules           | Public domain |
| SOX      | Yes — govinfo / Public Law 107-204                   | Core = §302/§404/§409/§802/§906 + more  | Public domain |
| PCI-DSS  | Restricted — © PCI SSC (v4.0.1)                       | 12 requirements / ~300 sub-reqs         | Copyright |
| RBI      | Yes — rbi.org.in, many Master Directions/circulars   | Unbounded, ever-changing                | Not one document |
| SEBI     | Yes — sebi.gov.in, many regulations                  | Large, multi-document                   | Not one document |

## Plan (when implemented — cost attached)

### A. Schema upgrade (lands first)
- Add `version`, `effective_date`, `source_url` to frontmatter + the `Policy` model.
- New `PolicyClause` table (`policy_id`, `section`, `citation`, `text`, `ord`) so exact
  clause text/citations live in Postgres (today: Qdrant-only) → precise display, future
  admin UI, clean re-seed. One Alembic async migration.
- Seed writes clauses to both Postgres (`PolicyClause`) and Qdrant.

### B. Acquisition toolkit (`backend/scripts/fetch/`, one fetcher per source)
- `gdpr.py` — EUR-Lex consolidated XML → one clause per Article, citation `GDPR Art. N`.
- `hipaa.py` — eCFR API (45 CFR 164, +160/162) → clause per §, citation `45 CFR §164.xxx`.
- `sox.py` — govinfo/USC → key sections, citation `SOX §404`.
- `rbi.py` — download chosen Master Directions (PDF/HTML) → structured clauses,
  citation `RBI <Master Direction> ¶N`.
- `sebi.py` — download chosen regulations → structured clauses, citation
  `SEBI <Regulation> Reg. N`.
- `pci_dss.py` — authored faithful paraphrase, citation `PCI-DSS Req. N.x`.
- `common.py` — frontmatter writer, clause normalizer, citation builder. Raw downloads
  cached so parsing/re-seeding is offline + reproducible.

### C. Chunking
- Raise the **policy** chunk size to ~1300/200 (legal clauses run long) without touching
  the document-analysis chunker.

### D. Embed & seed
- Reuse the idempotent seed script. Scale ≈ a few thousand clauses → a few thousand
  `text-embedding-3-small` calls (cents to low single-dollar, batched), reported per
  regulation.

### E. Verification (critical)
- Count assertions vs official (GDPR = 99 Articles, etc.); human spot-check for fidelity
  and citation accuracy. `scripts/verify_corpus.py` + `make seed-policies` print
  clauses/chunks per regulation.

### F. Maintenance
- Documented re-fetch/re-seed; optional scheduled refresh for RBI/SEBI (they change often).

## Phasing
1. **Phase A** — schema/migration + `PolicyClause`, chunk tuning, then GDPR + HIPAA + SOX
   (verbatim, fetched, verified).
2. **Phase B** — RBI + SEBI default set (fetch sources → structured clauses).
3. **Phase C** — PCI-DSS paraphrase.

## Execution notes
- **Network:** fetchers hit external sites (EUR-Lex/eCFR/govinfo/rbi.org.in/sebi.gov.in);
  run where there is internet (container or dev machine).
- **Cost:** embeddings only; small but non-zero — hence deferred until ready.
