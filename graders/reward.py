def compute_reward(
    task_score: float,
    step: int,
    max_steps: int,
    done: bool
) -> float:
    """
    Shaped reward function for SQL Antigravity Environment.

    Components:
      primary    = task_score x 0.70  (main quality signal)
      penalty    = step x -0.05       (encourages decisiveness)
      efficiency = up to +0.20        (bonus for solving fast)
      completion = +0.10              (bonus for finishing)

    Examples:
      Perfect on step 1: 0.70 - 0.05 + 0.20 + 0.10 = 0.95
      Perfect on step 2: 0.70 - 0.10 + 0.13 + 0.10 = 0.83
      Perfect on step 3: 0.70 - 0.15 + 0.07 + 0.10 = 0.72
      Wrong verdict:     0.00 - 0.05 + 0.00 + 0.00 = 0.00
    """
    reward = task_score * 0.70
    reward -= step * 0.05

    if done:
        efficiency = max(0.0, (max_steps - step) / max_steps)
        reward += efficiency * 0.20
        reward += 0.10

    return round(max(0.0, min(1.0, reward)), 4)
