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
            notes.append("correct verdict: reject")
        elif verdict == "needs_changes":
            score += 0.2
            notes.append("partially correct verdict")
        else:
            notes.append(f"wrong verdict: got '{verdict}', expected 'reject'")

        combined = " ".join(issues_found).lower()

        keyword_hits = sum(1 for kw in [
            "syntax", "typo", "misspell", "selct", "form",
            "wehre", "error", "incorrect", "keyword", "wrong"
        ] if kw in combined)

        specific_hits = sum(1 for kw in [
            "selct", "form", "wehre"
        ] if kw in combined)

        if specific_hits >= 2:
            score += 0.35
            notes.append("identified specific misspelled keywords")
        elif keyword_hits >= 2:
            score += 0.2
            notes.append("identified syntax issues generally")
        elif keyword_hits == 1:
            score += 0.1
            notes.append("partially identified issues")
        else:
            notes.append("missed syntax errors")

        if suggested_fix:
            fix_upper = suggested_fix.upper()
            has_select = "SELECT" in fix_upper
            has_from = "FROM" in fix_upper
            has_where = "WHERE" in fix_upper
            fix_count = sum([has_select, has_from, has_where])
            if fix_count == 3:
                score += 0.25
                notes.append("fix corrects all 3 keywords")
            elif fix_count == 2:
                score += 0.15
                notes.append("fix corrects 2 keywords")
            elif fix_count == 1:
                score += 0.05
                notes.append("fix partially correct")

        return min(score, 1.0), " | ".join(notes)


class PerformanceTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "needs_changes":
            score += 0.35
            notes.append("correct verdict: needs_changes")
        elif verdict == "reject":
            score += 0.2
            notes.append("acceptable verdict: reject")
        else:
            notes.append(f"wrong verdict: got '{verdict}'")

        combined = " ".join(issues_found).lower()

        star_hit = any(k in combined for k in [
            "select *", "wildcard", "all columns",
            "star", "select all", "unnecessary columns"
        ])
        where_hit = any(k in combined for k in [
            "where", "filter", "full scan", "full table scan",
            "no condition", "no filter", "missing filter",
            "without filter", "unfiltered"
        ])
        perf_hit = any(k in combined for k in [
            "performance", "slow", "inefficient",
            "million", "50m", "large table", "index"
        ])

        if star_hit:
            score += 0.2
            notes.append("caught SELECT *")
        else:
            notes.append("missed SELECT * issue")

        if where_hit:
            score += 0.2
            notes.append("caught missing WHERE clause")
        else:
            notes.append("missed missing WHERE clause")

        if perf_hit:
            score += 0.1
            notes.append("identified performance impact")

        if suggested_fix:
            fix_upper = suggested_fix.upper()
            has_where = "WHERE" in fix_upper
            no_star = "SELECT *" not in fix_upper
            has_cols = no_star and "SELECT" in fix_upper
            if has_where and has_cols:
                score += 0.15
                notes.append("fix uses specific columns and WHERE")
            elif has_where:
                score += 0.08
                notes.append("fix adds WHERE clause")

        return min(score, 1.0), " | ".join(notes)


class SecurityTask(Task):
    def grade(self, verdict, issues_found, suggested_fix=None):
        score = 0.0
        notes = []

        if verdict == "reject":
            score += 0.35
            notes.append("correct verdict: reject")
        elif verdict == "needs_changes":
            score += 0.15
            notes.append("partially correct verdict")
        else:
            notes.append(f"wrong verdict: got '{verdict}', expected 'reject'")

        combined = " ".join(issues_found).lower()

        injection_hits = sum(1 for k in [
            "sql injection", "injection", "unsanitized",
            "user input", "f-string", "f string",
            "string interpolat", "concatenat",
            "format string", "unescaped", "direct parameter"
        ] if k in combined)

        param_hits = sum(1 for k in [
            "parameteriz", "prepared statement", "bind param",
            "placeholder", "escaped", "sanitiz"
        ] if k in combined)

        if injection_hits >= 3:
            score += 0.4
            notes.append("thoroughly identified SQL injection")
        elif injection_hits == 2:
            score += 0.3
            notes.append("clearly identified SQL injection")
        elif injection_hits == 1:
            score += 0.15
            notes.append("partially identified injection risk")
        else:
            notes.append("missed SQL injection vulnerability")

        if param_hits >= 1:
            score += 0.15
            notes.append("recommended parameterized queries")
        else:
            notes.append("did not recommend parameterized queries")

        if suggested_fix:
            has_param = any(k in suggested_fix for k in [
                "%s", "?", ":param", ":username",
                "execute(query, (", "cursor.execute"
            ])
            no_fstring = "f\"" not in suggested_fix and "f'" not in suggested_fix
            if has_param and no_fstring:
                score += 0.1
                notes.append("fix correctly uses parameterized query")
            elif has_param:
                score += 0.05
                notes.append("fix attempts parameterization")

        return min(score, 1.0), " | ".join(notes)


TASK_ORDER = ["task_easy", "task_medium", "task_hard"]

TASKS = {
    "task_easy": SyntaxTask(
        task_id="task_easy",
        difficulty="easy",
        query="SELCT name, email FORM users WEHRE id = 1",
        schema_context=(
            "Table: users(id INT PK, name VARCHAR(100), "
            "email VARCHAR(200), created_at TIMESTAMP)"
        ),
        task_description=(
            "A developer wrote this query to fetch name and email "
            "for user id=1. Review it for correctness before it "
            "goes to production."
        ),
        correct_verdict="reject",
    ),
    "task_medium": PerformanceTask(
        task_id="task_medium",
        difficulty="medium",
        query="SELECT * FROM orders",
        schema_context=(
            "Table: orders(id INT PK, user_id INT FK, "
            "product_id INT FK, amount DECIMAL(10,2), "
            "status VARCHAR(20), created_at TIMESTAMP) "
            "— approximately 50 million rows, no query cache"
        ),
        task_description=(
            "This query powers the today's pending orders "
            "dashboard widget. It runs every 30 seconds. "
            "Review it for performance and correctness."
        ),
        correct_verdict="needs_changes",
    ),
    "task_hard": SecurityTask(
        task_id="task_hard",
        difficulty="hard",
        query=(
            'def get_user(username):\n'
            '    query = f"SELECT * FROM users '
            'WHERE username = \'{username}\'"\n'
            '    return db.execute(query)'
        ),
        schema_context=(
            "Table: users(id INT PK, username VARCHAR(50) UNIQUE, "
            "password_hash VARCHAR(255), role VARCHAR(20), "
            "last_login TIMESTAMP) "
            "— production authentication table"
        ),
        task_description=(
            "This Python function is used in the login endpoint "
            "to fetch users by username. It was written by a junior "
            "developer. Review the embedded SQL for security issues "
            "before merging to main."
        ),
        correct_verdict="reject",
    ),
}
