from typing import Any, Dict
from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from core.models import SQLReviewAction, SQLReviewObservation

class SQLAntigravityClient(EnvClient[SQLReviewAction, SQLReviewObservation, State]):
    def _step_payload(self, action: SQLReviewAction) -> Dict[str, Any]:
        return action.model_dump()

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[SQLReviewObservation]:
        obs_data = payload.get("observation", {})
        obs = SQLReviewObservation(**obs_data)
        return StepResult(
            observation=obs,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False)
        )

    def _parse_state(self, payload: Dict[str, Any]) -> State:
        return State(**payload)
