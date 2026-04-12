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

    def grade(self, verdict: str, issues_found: List[str],
              suggested_fix: str = None) -> Tuple[float, str]:
        raise NotImplementedError


class SyntaxTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "reject":
            score += 0.4
            notes.append("correct verdict")
        elif verdict == "needs_changes":
            score += 0.2
            notes.append("acceptable verdict")
        else:
            notes.append("wrong verdict")

        combined = " ".join(issues_found).lower()

        specific = sum(1 for k in ["selct", "form", "wehre", "typo", "misspell"] if k in combined)
        general = sum(1 for k in ["syntax", "error", "incorrect", "keyword", "wrong"] if k in combined)

        if specific >= 2:
            score += 0.4
            notes.append("identified specific keywords")
        elif specific >= 1 or general >= 2:
            score += 0.25
            notes.append("identified issues")
        elif general >= 1:
            score += 0.1
            notes.append("partial identification")

        if suggested_fix:
            fix = suggested_fix.upper()
            if "SELECT" in fix and "FROM" in fix and "WHERE" in fix:
                score += 0.2
                notes.append("fix corrects all keywords")
            elif "SELECT" in fix and "FROM" in fix:
                score += 0.1
                notes.append("fix partially correct")

        return min(score, 0.97), " | ".join(notes)


class PerformanceTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "needs_changes":
            score += 0.35
            notes.append("correct verdict")
        elif verdict == "reject":
            score += 0.2
            notes.append("acceptable verdict")
        else:
            notes.append("wrong verdict")

        combined = " ".join(issues_found).lower()

        star_hit = any(k in combined for k in [
            "select *", "select star", "star", "wildcard",
            "all columns", "unnecessary columns", "fetches all"
        ])
        where_hit = any(k in combined for k in [
            "where", "filter", "full scan", "full table",
            "no filter", "missing filter", "without filter",
            "unfiltered", "no condition"
        ])
        perf_hit = any(k in combined for k in [
            "performance", "slow", "inefficient", "50m",
            "million", "large table", "resource"
        ])

        if star_hit:
            score += 0.2
            notes.append("caught SELECT star")
        if where_hit:
            score += 0.2
            notes.append("caught missing WHERE")
        if perf_hit:
            score += 0.1
            notes.append("noted performance impact")

        if suggested_fix:
            fix = suggested_fix.upper()
            if "WHERE" in fix and "SELECT *" not in fix:
                score += 0.15
                notes.append("fix correct")

        return min(score, 0.97), " | ".join(notes)


class SecurityTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "reject":
            score += 0.35
            notes.append("correct verdict")
        elif verdict == "needs_changes":
            score += 0.15
            notes.append("acceptable verdict")
        else:
            notes.append("wrong verdict")

        combined = " ".join(issues_found).lower()

        inj = sum(1 for k in [
            "sql injection", "injection", "f-string",
            "f string", "interpolat", "concatenat",
            "unsanitized", "user input", "direct", "string"
        ] if k in combined)

        param = sum(1 for k in [
            "parameteriz", "prepared", "placeholder",
            "sanitiz", "escaped", "%s"
        ] if k in combined)

        if inj >= 3:
            score += 0.4
            notes.append("thoroughly identified injection")
        elif inj >= 2:
            score += 0.3
            notes.append("identified injection")
        elif inj >= 1:
            score += 0.15
            notes.append("partial injection")

        if param >= 1:
            score += 0.15
            notes.append("recommended parameterized")

        if suggested_fix:
            if "%s" in suggested_fix or ":param" in suggested_fix:
                score += 0.1
                notes.append("fix uses parameterization")

        return min(score, 0.97), " | ".join(notes)


class ExpertTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "reject":
            score += 0.30
            notes.append("correct verdict")
        elif verdict == "needs_changes":
            score += 0.15
            notes.append("acceptable verdict")
        else:
            notes.append("wrong verdict")

        combined = " ".join(issues_found).lower()

        inj_hits = sum(1 for k in [
            "injection", "f-string", "f string", "interpolat",
            "concatenat", "unsanitized", "user_id", "direct"
        ] if k in combined)

        perf_hits = sum(1 for k in [
            "select *", "star", "wildcard", "all columns",
            "index", "full scan", "50 million", "performance"
        ] if k in combined)

        param_hits = sum(1 for k in [
            "parameteriz", "prepared", "placeholder", "%s", "sanitiz"
        ] if k in combined)

        if inj_hits >= 2:
            score += 0.25
            notes.append("identified injection")
        elif inj_hits == 1:
            score += 0.12
            notes.append("partial injection")

        if perf_hits >= 2:
            score += 0.20
            notes.append("identified performance issues")
        elif perf_hits == 1:
            score += 0.10
            notes.append("partial performance")

        if param_hits >= 1:
            score += 0.15
            notes.append("recommended parameterized")

        if suggested_fix:
            has_param = any(k in suggested_fix for k in ["%s", "?", ":param"])
            no_star = "SELECT *" not in suggested_fix.upper()
            if has_param and no_star:
                score += 0.10
                notes.append("fix correct")

        return min(score, 0.97), " | ".join(notes)


TASK_ORDER = ["task_easy", "task_medium", "task_hard", "task_expert"]

TASKS = {
    "task_easy": SyntaxTask(
        task_id="task_easy",
        difficulty="easy",
        query="SELCT name, email FORM users WEHRE id = 1",
        schema_context="Table: users(id INT PK, name VARCHAR(100), email VARCHAR(200), created_at TIMESTAMP)",
        task_description="A developer wrote this query to fetch name and email for user id=1. Review it for correctness before it goes to production.",
        correct_verdict="reject",
    ),
    "task_medium": PerformanceTask(
        task_id="task_medium",
        difficulty="medium",
        query="SELECT * FROM orders",
        schema_context="Table: orders(id INT PK, user_id INT FK, product_id INT FK, amount DECIMAL(10,2), status VARCHAR(20), created_at TIMESTAMP) — approximately 50 million rows, no query cache",
        task_description="This query powers the today's pending orders dashboard widget. It runs every 30 seconds. Review it for performance and correctness.",
        correct_verdict="needs_changes",
    ),
    "task_hard": SecurityTask(
        task_id="task_hard",
        difficulty="hard",
        query='def get_user(username):\n    query = f"SELECT * FROM users WHERE username = \'{username}\'"\n    return db.execute(query)',
        schema_context="Table: users(id INT PK, username VARCHAR(50) UNIQUE, password_hash VARCHAR(255), role VARCHAR(20), last_login TIMESTAMP) — production authentication table",
        task_description="This Python function is used in the login endpoint to fetch users by username. It was written by a junior developer. Review the embedded SQL for security issues before merging to main.",
        correct_verdict="reject",
    ),
    "task_expert": ExpertTask(
        task_id="task_expert",
        difficulty="expert",
        query=(
            'def get_orders(user_id, status):\n'
            '    query = f"SELECT * FROM orders WHERE user_id = {user_id}"\n'
            '    if status:\n'
            '        query += f" AND status = \'{status}\'"\n'
            '    return db.execute(query)'
        ),
        schema_context=(
            "Table: orders(id INT PK, user_id INT FK, product_id INT FK, "
            "amount DECIMAL(10,2), status VARCHAR(20), created_at TIMESTAMP) "
            "— 50 million rows, user_id has index, no status index"
        ),
        task_description=(
            "This Python function fetches orders by user and optionally filters by status. "
            "It runs on every page load of the order history page. "
            "Review for ALL issues: security, performance, and correctness."
        ),
        correct_verdict="reject",
    ),
}
