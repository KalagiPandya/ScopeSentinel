# ScopeSentinel - Placement Pitch and Interview Prep (Day 18)

---

## 30-Second Elevator Pitch

"I built ScopeSentinel - an 8-agent AI platform that solves requirement
drift and requirement-to-code traceability. It watches meetings, emails,
Jira, and GitHub 24/7. It detects requirement changes, maps them to
actual code using a Coverage Score, reviews every Pull Request for
compliance, and alerts teams within seconds with full impact analysis
and risk scoring. Every software company loses money to missed
requirements - ScopeSentinel prevents that automatically."

---

## The Problem (Say This First)

Three things go wrong on every real software project:
1. Requirements change in conversation, not in writing - nobody updates the docs
2. Even tracked requirements aren't verified against the actual code
3. Managers can't answer "what percent of requirements are actually done?"

---

## What Makes It Unique

| Most tools do this | ScopeSentinel does this |
|---|---|
| Track tickets (Jira) | Detect requirement drift automatically from raw conversation |
| Help write code (Copilot) | Verify code against requirements - Coverage Score |
| Review code style (CodeRabbit) | Review requirement compliance per PR |

The combination - drift detection + code-to-requirement traceability +
graph-based impact analysis - is what makes this stand out in a student
portfolio.

---

## Architecture Talking Points

8 AI Agents, 3 LangGraph Pipelines:

```
Main pipeline:    Extractor -> Detector -> Impact(BFS) -> Risk -> Notifier
GitHub pipeline:  Repo Scanner -> Coverage Mapper
PR pipeline:      PR Compliance Reviewer
```

Tech stack: FastAPI, React, LangGraph, Qdrant (vector search), Neo4j
(graph/BFS), PostgreSQL, Redis, PyGithub, OpenAI GPT-4o-mini, Docker.

---

## Key Interview Q&A

Q: How does Agent 2 detect a requirement changed if the wording is
completely different?

A: I embed every requirement using OpenAI's text-embedding-3-small
model and store vectors in Qdrant. When new text comes in, I do a
cosine similarity search. Above 0.92 similarity means same requirement,
no change. 0.60-0.92 means modification (I run a Myers diff to show
exactly which words changed). Below 0.60 is treated as a brand new
requirement.

Q: How does the Coverage Score actually work - does it read all the code?

A: No, that would burn too many tokens. Agent 3 first does a lightweight
scan: it lists every file path in the repo via the GitHub API and
classifies each one (frontend/backend/database/test) using path and
extension heuristics. Agent 4 then sends the requirement text plus this
classified file list to an LLM, which reasons about what's likely
implemented based on naming patterns - seeing otp_service.py and
OTPInput.jsx strongly suggests OTP login is implemented, but the LLM
can also flag what's conspicuously missing, like no test file or no
expiry logic file.

Q: Why Neo4j instead of just storing relationships in Postgres?

A: Impact analysis is inherently a graph traversal problem - find every
module reachable from this requirement within 3 hops. That's a natural
BFS query in Cypher. Doing the same with recursive SQL joins in
Postgres would be much messier and slower at scale.

Q: What was the hardest bug you fixed?

A: Early on, the Postgres Docker container kept failing with a password
mismatch. The cause turned out to be a stale Docker volume holding
credentials from an earlier run - Docker doesn't reinitialize a volume
just because docker-compose.yml changed. I fixed it by giving the
volume a unique name and wrote a reset script that fully tears down and
recreates containers and volumes, so the setup is reproducible for
anyone cloning the repo.

Q: What would you build next?

A: Two things: Jira/Confluence integration so drift detection covers
formally-tracked tickets too, not just conversational sources, and a
feedback loop where developer corrections to the Coverage Score get
stored and used to improve the matching prompts over time.

---

## DSA You Can Discuss

| Concept | Where Used |
|---|---|
| Directed Graph + BFS | Neo4j requirement-module impact traversal |
| Cosine similarity / KNN | Qdrant semantic requirement matching |
| LCS / Myers-style diff | Word-level change visualization |
| Hash Map | AgentState lookups, requirement deduplication |
| DAG | LangGraph pipeline structure (StateGraph) |

---

## Resume Bullet (Copy-Paste Ready)

Built ScopeSentinel, an 8-agent AI platform (LangGraph, FastAPI, React)
that detects requirement drift across meetings/documents using semantic
embeddings (Qdrant), performs graph-based impact analysis (Neo4j BFS),
calculates a Requirement-to-Code Coverage Score by analyzing GitHub
repositories, reviews Pull Requests for requirement compliance, and
routes risk-scored alerts - reducing rework from undocumented scope
changes.

---

## Demo Script for Interviews (5 minutes)

1. (30s) Show the Dashboard - KPIs, risk chart, coverage breakdown
2. (90s) Go to Upload Center, paste a meeting transcript live, click
   Run Pipeline - narrate what each agent is doing as results stream in
3. (60s) Go to Change Center - point out the word-level diff
4. (60s) Go to GitHub Center - scan a real repo, show file classification
5. (60s) Go to Coverage Center - click a requirement, show found/missing
6. (30s) Close with: "This is the question nobody else answers - did
   the code actually implement the requirement?"

Or run python scripts/demo_story.py for a narrated terminal walkthrough
if you don't have screen-share set up.
