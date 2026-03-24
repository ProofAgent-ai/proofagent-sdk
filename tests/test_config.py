from proofagent.config import ProofAgentConfig


def test_config_defaults_from_constructor():
    cfg = ProofAgentConfig(api_key="apk_live_xxx")
    assert cfg.base_url == "https://api.proofagent.ai"
    assert cfg.max_retries == 3
