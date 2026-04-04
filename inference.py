import os
import json
import re
import sys

from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

print(f"Using model: {MODEL_NAME}")
print(f"Using API: {API_BASE_URL}")
print(f"Token set: {'yes' if API_KEY else 'NO - MISSING'}")

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """You are an expert SQL security and performance reviewer.
You will be shown a SQL query with schema context.
Respond ONLY with valid JSON — no explanation, no markdown:
{
  "verdict": "approve" or "reject" or "needs_changes",
  "issues_found": ["describe each issue clearly"],
  "suggested_fix": "corrected SQL or null"
}"""


def call_llm(user_msg: str) -> dict:
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        raw = resp.choices[0].message.content.strip()
        print(f"LLM raw response: {raw[:100]}...")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
            return {"verdict": "approve", "issues_found": [], "suggested_fix": None}
    except Exception as e:
        print(f"LLM call failed: {e}")
        return {"verdict": "approve", "issues_found": [], "suggested_fix": None}


def run_baseline():
    sys.path.insert(0, os.path.dirname(__file__))

    from env.sql_environment import SQLAntigravityEnvironment
    from tasks.task_definitions import TASK_ORDER, TASKS
    from core.models import SQLReviewAction

    print("\n=== SQL Antigravity Env — Baseline Run ===\n")

    env = SQLAntigravityEnvironment()
    obs = env.reset()

    current_task_id = obs.task_id
    task_rewards = {tid: 0.0 for tid in TASK_ORDER}

    for global_step in range(20):
        if obs.done or obs.task_id == "done":
            break

        print(f"\n--- Step {global_step+1} | Task: {current_task_id} ---")
        print(f"Query: {obs.query[:80]}...")

        user_msg = (
            f"Task: {obs.task_description}\n\n"
            f"Schema:\n{obs.schema_context}\n\n"
            f"SQL to review:\n```sql\n{obs.query}\n```"
            + (f"\n\nPrevious feedback: {obs.feedback}" if obs.feedback else "")
        )

        data = call_llm(user_msg)
        print(f"Agent verdict: {data.get('verdict')}")
        print(f"Issues found: {data.get('issues_found')}")

        action = SQLReviewAction(
            verdict=data.get("verdict", "approve"),
            issues_found=data.get("issues_found", []),
            suggested_fix=data.get("suggested_fix"),
        )

        obs = env.step(action)
        task_rewards[current_task_id] = (
            task_rewards.get(current_task_id, 0.0) + (obs.reward or 0.0)
        )

        print(f"Reward: {obs.reward} | Done: {obs.done}")

        if obs.task_id != current_task_id:
            print(f"\n>>> Moving to next task: {obs.task_id}")
            current_task_id = obs.task_id

    print("\n=== Final Results ===")
    total = 0.0
    for tid in TASK_ORDER:
        diff = TASKS[tid].difficulty
        r = round(task_rewards[tid], 3)
        total += r
        print(f"  {tid} ({diff}): reward = {r}")
    print(f"  Total reward: {round(total, 3)}")
    print("\n=== Baseline Complete ===")


if __name__ == "__main__":
    run_baseline()
