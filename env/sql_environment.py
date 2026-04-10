import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uuid
from typing import Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from core.models import SQLReviewAction, SQLReviewObservation
from tasks.task_definitions import TASKS, TASK_ORDER
from graders.reward import compute_reward

MAX_STEPS_PER_TASK = 3


class SQLAntigravityEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        super().__init__()
        self._episode_id = None
        self._step_count = 0
        self._task_index = 0
        self._steps_this_task = 0
        self._done = False
        self._total_score = 0.0

    @property
    def state(self) -> State:
        return State(
            episode_id=self._episode_id,
            step_count=self._step_count,
            current_task_id=(TASK_ORDER[self._task_index] if not self._done else "done"),
            tasks_completed=self._task_index,
            total_score=round(self._total_score / max(1, self._step_count), 4),
        )

    def reset(self, seed=None, episode_id=None, **kwargs):
        self._episode_id = episode_id or str(uuid.uuid4())
        self._step_count = 0
        self._task_index = 0
        self._steps_this_task = 0
        self._done = False
        self._total_score = 0.0
        task = TASKS[TASK_ORDER[0]]
        return SQLReviewObservation(
            query=task.query,
            schema_context=task.schema_context,
            task_description=task.task_description,
            task_id=task.task_id,
            step_num=0,
            feedback=None,
            done=False,
            reward=None,
        )

    def step(self, action: SQLReviewAction, timeout_s=None, **kwargs):
        self._step_count += 1
        self._steps_this_task += 1
        task_key = TASK_ORDER[self._task_index]
        task = TASKS[task_key]
        score, feedback_text = task.grade(
            verdict=action.verdict,
            issues_found=action.issues_found,
            suggested_fix=action.suggested_fix,
        )
        self._total_score += score
        task_done = (
            self._steps_this_task >= MAX_STEPS_PER_TASK
            or score >= 0.90
        )
        reward = compute_reward(score, self._steps_this_task, MAX_STEPS_PER_TASK, task_done)
        if task_done:
            self._task_index += 1
            self._steps_this_task = 0
            if self._task_index >= len(TASK_ORDER):
                self._done = True
                return SQLReviewObservation(
                    query="All tasks complete.",
                    schema_context="",
                    task_description="Episode finished.",
                    task_id="done",
                    step_num=self._step_count,
                    feedback=f"Final task score: {score:.2f} | {feedback_text}",
                    done=True,
                    reward=reward,
                )
            else:
                next_task = TASKS[TASK_ORDER[self._task_index]]
                return SQLReviewObservation(
                    query=next_task.query,
                    schema_context=next_task.schema_context,
                    task_description=next_task.task_description,
                    task_id=next_task.task_id,
                    step_num=0,
                    feedback=f"Task '{task_key}' score: {score:.2f} | {feedback_text}",
                    done=False,
                    reward=reward,
                )
        else:
            return SQLReviewObservation(
                query=task.query,
                schema_context=task.schema_context,
                task_description=task.task_description,
                task_id=task.task_id,
                step_num=self._steps_this_task,
                feedback=f"Score so far: {score:.2f} | {feedback_text} | Try again.",
                done=False,
                reward=reward,
            )
