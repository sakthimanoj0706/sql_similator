def compute_reward(task_score: float, step: int, max_steps: int, done: bool) -> float:
    reward = task_score * 0.75
    reward -= step * 0.05
    if done:
        efficiency = max(0.0, (max_steps - step) / max_steps)
        reward += efficiency * 0.15
        reward += 0.10
    return round(max(0.0, min(1.0, reward)), 4)
