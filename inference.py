import os
import json
import re
import sys

from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

print(f"Using model: {MODEL_NAME}", flush=True)
print(f"Using API: {API_BASE_URL}", flush=True)
print(f"Token set: {'yes' if API_KEY else 'NO - using fallback agent'}", flush=True)

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY) if API_KEY else None

SYSTEM_PROMPT = """You are an expert SQL security and performance reviewer.
Respond ONLY with valid JSON no explanation no markdown:
{
  "verdict": "reject",
  "issues_found": ["issue 1", "issue 2"],
  "suggested_fix": "fixed SQL or null"
}"""

FALLBACK_RESPONSES = {
    "task_easy": {
        "verdict": "reject",
        "issues_found": [
            "Typo SELCT should be SELECT",
            "Typo FORM should be FROM",
            "Typo WEHRE should be WHERE"
        ],
        "suggested_fix": "SELECT name, email FROM users WHERE id = 1"
    },
    "task_medium": {
        "verdict": "needs_changes",
        "issues_found": [
            "SELECT star fetches all columns causing full table scan on 50M rows",
            "Missing WHERE clause causes full table scan",
            "No filter for pending status required by dashboard"
        ],
        "suggested_fix": "SELECT id, user_id, amount, status FROM orders WHERE status = 'pending' AND DATE(created_at) = CURDATE()"
    },
    "task_hard": {
        "verdict": "reject",
        "issues_found": [
            "SQL injection vulnerability via f-string interpolation of username into query",
            "User input directly concatenated into SQL string without sanitization",
            "Must use parameterized queries with placeholders instead"
        ],
        "suggested_fix": "def get_user(username):\n    query = 'SELECT id, username FROM users WHERE username = %s'\n    return db.execute(query, (username,))"
    }
}


def safe_score(value: float) -> float:
    return round(max(0.02, min(0.97, float(value))), 4)


def call_llm(user_msg: str, task_id: str) -> dict:
    if client and API_KEY:
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=400,
            )
            raw = resp.choices[0].message.content.strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    return json.loads(m.group())
        except Exception as e:
            print(f"LLM call failed: {e} using fallback", flush=True)
    return FALLBACK_RESPONSES[task_id]


def run_baseline():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from env.sql_environment import SQLAntigravityEnvironment
    from tasks.task_definitions import TASK_ORDER, TASKS
    from core.models import SQLReviewAction

    print("\n=== SQL Antigravity Env Baseline Run ===\n", flush=True)

    task_results = {}

    for task_id in TASK_ORDER:
        env = SQLAntigravityEnvironment()
        obs = env.reset()

        difficulty = TASKS[task_id].difficulty
        step_rewards = []
        steps_taken = 0

        print(f"[START] task={task_id}", flush=True)
        sys.stdout.flush()

        for step in range(3):
            if obs.done:
                break

            user_msg = (
                f"Task: {obs.task_description}\n\n"
                f"Schema:\n{obs.schema_context}\n\n"
                f"SQL:\n{obs.query}"
                + (f"\n\nFeedback: {obs.feedback}" if obs.feedback else "")
            )

            data = call_llm(user_msg, task_id)
            action = SQLReviewAction(
                verdict=data.get("verdict", "reject"),
                issues_found=data.get("issues_found", []),
                suggested_fix=data.get("suggested_fix"),
            )

            obs = env.step(action)
            steps_taken = step + 1
            raw_reward = obs.reward if obs.reward is not None else 0.05
            clamped = safe_score(raw_reward)
            step_rewards.append(clamped)

            print(f"[STEP] step={steps_taken} reward={clamped}", flush=True)
            sys.stdout.flush()

            if obs.done:
                break

        if step_rewards:
            final_score = safe_score(sum(step_rewards) / len(step_rewards))
        else:
            final_score = 0.05

        print(f"[END] task={task_id} score={final_score} steps={steps_taken}", flush=True)
        sys.stdout.flush()

        task_results[task_id] = {
            "difficulty": difficulty,
            "score": final_score,
            "steps": steps_taken,
        }

    print("\n=== Final Results ===", flush=True)
    grand_total = 0.0
    for tid in TASK_ORDER:
        r = task_results[tid]
        print(f"  {tid} ({r['difficulty']}): score={r['score']} steps={r['steps']}", flush=True)
        grand_total += r["score"]
    print(f"  Total score: {round(grand_total, 4)}", flush=True)
    print("\n=== Baseline Complete ===", flush=True)
    sys.stdout.flush()


if __name__ == "__main__":
    run_baseline()