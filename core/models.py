import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Optional, List
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class SQLReviewAction(Action):
    verdict: str = Field(..., description="One of: approve, reject, needs_changes")
    issues_found: List[str] = Field(default_factory=list, description="List of issues identified")
    suggested_fix: Optional[str] = Field(default=None, description="Corrected SQL query optional")


class SQLReviewObservation(Observation):
    query: str = Field(..., description="SQL query to review")
    schema_context: str = Field(..., description="Table schema")
    task_description: str = Field(..., description="What the query should do")
    task_id: str = Field(..., description="Current task identifier")
    step_num: int = Field(default=0, description="Attempt number")
    feedback: Optional[str] = Field(default=None, description="Feedback from previous attempt")
