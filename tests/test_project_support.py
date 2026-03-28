import asyncio

import pytest

from proofagent.exceptions import ProofAgentError
from proofagent.project_support import assert_project_supports_logs


class FakeClient:
    def __init__(self, mode: str):
        self._mode = mode

    async def get_project_context(self):
        return {
            "data": {
                "project": {
                    "name": "p",
                    "mode": self._mode,
                }
            }
        }


def test_assert_project_supports_logs_accepts_log_replay():
    ctx = asyncio.run(assert_project_supports_logs(FakeClient("log_replay")))
    assert ctx["data"]["project"]["mode"] == "log_replay"


def test_assert_project_supports_logs_rejects_judge_led():
    with pytest.raises(ProofAgentError):
        asyncio.run(assert_project_supports_logs(FakeClient("judge_led")))
