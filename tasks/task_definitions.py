from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Task:
    task_id: str
    difficulty: str
    query: str
    schema_context: str
    task_description: str
    correct_verdict: str

    def grade(self, verdict: str, issues_found: List[str], suggested_fix: str = None) -> Tuple[float, str]:
        raise NotImplementedError


class SyntaxTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []
        if verdict == "reject":
            score += 0.4
            notes.append("[Verdict] Correct: 'reject'.")
        else:
            notes.append(f"[Verdict] Incorrect: Expected 'reject', but got '{verdict}'.")
        combined = " ".join(issues_found).lower()
        hits = sum(1 for kw in ["syntax error", "typo", "misspelled keyword", "selct", "form", "wehre"] if kw in combined)
        if hits >= 2:
            score += 0.4
            notes.append("[Analysis] Identified multiple syntax errors.")
        elif hits == 1:
            score += 0.2
            notes.append("[Analysis] Partially identified syntax issues.")
        else:
            notes.append("[Analysis] Missed key syntax errors (e.g., misspelled keywords).")
        if suggested_fix and "SELECT" in suggested_fix.upper() and "FROM" in suggested_fix.upper():
            score += 0.2
            notes.append("[Fix] Valid corrected query provided.")
        return min(score, 1.0), " ".join(notes)


class PerformanceTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []
        if verdict in ("reject", "needs_changes"):
            score += 0.3
            notes.append("[Verdict] Correct: Flagged for changes/rejection.")
        else:
            notes.append(f"[Verdict] Incorrect: Expected 'needs_changes' or 'reject', but got '{verdict}'.")
        combined = " ".join(issues_found).lower()
        if any(k in combined for k in ["select *", "wildcard", "all columns FETCH"]):
            score += 0.25
            notes.append("[Analysis] Correctly flagged 'SELECT *' usage.")
        else:
            notes.append("[Analysis] Missed 'SELECT *' performance anti-pattern.")
        if any(k in combined for k in ["missing where", "full table scan", "no execution filter", "no condition"]):
            score += 0.25
            notes.append("[Analysis] Correctly flagged missing WHERE clause.")
        else:
            notes.append("[Analysis] Missed missing WHERE clause (full scan risk).")
        if suggested_fix:
            fix_up = suggested_fix.upper()
            if "WHERE" in fix_up and "SELECT *" not in fix_up:
                score += 0.2
                notes.append("[Fix] Provided a performant query fix.")
        return min(score, 1.0), " ".join(notes)


class SecurityTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []
        if verdict == "reject":
            score += 0.3
            notes.append("[Verdict] Correct: Rejected due to security risk.")
        else:
            notes.append(f"[Verdict] Incorrect: Expected 'reject', but got '{verdict}'.")
        combined = " ".join(issues_found).lower()
        inj_hits = sum(1 for k in ["sql injection", "unsanitized input", "f-string vulnerability", "string concatenation", "format string"] if k in combined)
        if inj_hits >= 2:
            score += 0.4
            notes.append("[Analysis] Successfully identified SQL injection risk.")
        elif inj_hits == 1:
            score += 0.2
            notes.append("[Analysis] Partially identified unsanitized input risk.")
        else:
            notes.append("[Analysis] Missed critical SQL injection vulnerability.")
        if any(k in combined for k in ["parameterized query", "prepared statement", "bind parameter"]):
            score += 0.15
            notes.append("[Recommendation] Correctly suggested parameterized queries.")
        if suggested_fix and any(k in suggested_fix for k in ["%s", "?", ":param", "execute("]):
            score += 0.15
            notes.append("[Fix] Provided a safe string parameterized fix.")
        return min(score, 1.0), " ".join(notes)


TASK_ORDER = ["task_easy", "task_medium", "task_hard"]

TASKS = {
    "task_easy": SyntaxTask(
        task_id="task_easy",
        difficulty="easy",
        query="SELCT name, email FORM users WEHRE id = 1",
        schema_context="Table: users(id INT PK, name VARCHAR, email VARCHAR, created_at TIMESTAMP)",
        task_description="Fetch name and email for user id=1. Review this query for correctness.",
        correct_verdict="reject",
    ),
    "task_medium": PerformanceTask(
        task_id="task_medium",
        difficulty="medium",
        query="SELECT * FROM orders",
        schema_context="Table: orders(id INT PK, user_id INT FK, product_id INT FK, amount DECIMAL, status VARCHAR, created_at TIMESTAMP) — 50M rows",
        task_description="Get all pending orders for today's dashboard. Review for performance and correctness.",
        correct_verdict="needs_changes",
    ),
    "task_hard": SecurityTask(
        task_id="task_hard",
        difficulty="hard",
        query="def get_user(username):\n    query = f\"SELECT * FROM users WHERE username = '{username}'\"\n    return db.execute(query)",
        schema_context="Table: users(id INT PK, username VARCHAR, password_hash VARCHAR, role VARCHAR)",
        task_description="Python function fetching a user by username. Review the embedded SQL for security issues.",
        correct_verdict="reject",
    ),
}
