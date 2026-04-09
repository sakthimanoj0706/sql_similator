def compute_reward(
    task_score: float,
    step: int,
    max_steps: int,
    done: bool
) -> float:
    reward = task_score * 0.68
    reward -= step * 0.04
    if done:
        efficiency = max(0.0, (max_steps - step) / max_steps)
        reward += efficiency * 0.18
        reward += 0.08
    reward = max(0.02, min(0.97, reward))
    return round(reward, 4)
