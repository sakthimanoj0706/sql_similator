import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openenv.core.env_server.http_server import create_app
from core.models import SQLReviewAction, SQLReviewObservation
from env.sql_environment import SQLAntigravityEnvironment

app = create_app(
    env=SQLAntigravityEnvironment,
    action_cls=SQLReviewAction,
    observation_cls=SQLReviewObservation,
    env_name="sql-antigravity-env",
)
