---
title: SQL Antigravity Env
emoji: 🛢️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - sql
  - code-review
  - security
---

# SQL Antigravity Environment

A real-world **OpenEnv** environment where AI agents learn to review SQL queries — detecting syntax errors, performance anti-patterns, and security vulnerabilities.

Built for the **Meta PyTorch x Hugging Face OpenEnv Hackathon** by team Resq-Minds.

---

## Overview

Every software team writes SQL queries that need to be reviewed before going to production. This environment trains an AI agent to act as a senior SQL reviewer — reading a query, identifying problems, and submitting a structured review verdict.

---

## Action Space

The agent submits a JSON action:

```json
{
  "verdict": "approve" | "reject" | "needs_changes",
  "issues_found": ["list of identified issues"],
  "suggested_fix": "corrected SQL or null"
}
```

## Observation Space

The agent receives:
- `query` — the SQL query to review
- `schema_context` — table schema for context
- `task_description` — what the query is supposed to do
- `task_id` — current task identifier
- `step_num` — attempt number (max 3 per task)
- `feedback` — grader feedback from previous attempt

---

## Tasks description

| Task | Difficulty | Description |
|------|-----------|-------------|
| task_easy | Easy | Detect misspelled SQL keywords (SELCT, FORM, WEHRE) |
| task_medium | Medium | Identify SELECT * and missing WHERE clause on 50M row table |
| task_hard | Hard | Detect SQL injection via f-string interpolation |

---

## Reward Function

Shaped reward providing signal throughout the episode:

```
reward = (task_score × 0.75) − (step × 0.05) + efficiency_bonus + completion_bonus
```

- Primary signal: task score × 0.75
- Step penalty: −0.05 per attempt (encourages decisiveness)
- Efficiency bonus: up to +0.15 for solving on first attempt
- Completion bonus: +0.10 for finishing the task

---

## Baseline Scores

Tested with `meta-llama/Llama-3.1-8B-Instruct` via HuggingFace router:

| Task | Reward |
|------|--------|
| task_easy (easy) | 0.9 |
| task_medium (medium) | 0.9 |
| task_hard (hard) | 0.8 |
| **Total** | **2.6** |

---

## Quick Start

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)
```

## API usage (/reset, /step)

You can interact with the environment using REST APIs:
- `POST /reset` — start new episode
- `POST /step` — submit action

Additional endpoints:
- `GET /health` — health check
- `GET /schema` — action and observation schemas
- `GET /state` — current episode state
- `WebSocket /ws` — persistent session interface

---

## How to run locally

```bash
git clone https://github.com/sakthimanoj0706/sql_simulator
cd sql_simulator
pip install -r requirements.txt
uvicorn app.server:app --host 0.0.0.0 --port 8000
```

## Run Inference

```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
python inference.py
```
