def compute_reward(
    task_score: float,
    step: int,
    max_steps: int,
    done: bool
) -> float:
    """
    Shaped reward — always returns strictly between 0.01 and 0.99
    Never exactly 0.0 or 1.0 as required by OpenEnv validator.
    """
    reward = task_score * 0.70
    reward -= step * 0.05

    if done:
        efficiency = max(0.0, (max_steps - step) / max_steps)
        reward += efficiency * 0.20
        reward += 0.10

    reward = max(0.01, min(0.99, reward))
    return round(reward, 4)
