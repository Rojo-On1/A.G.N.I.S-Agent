from agnis.agents import (
    CLASSIFIER_PARAMETERS,
    IMPACT_PARAMETERS,
    NORMALIZER_PARAMETERS,
)


def test_agent_parameters_prioritize_precision() -> None:
    assert NORMALIZER_PARAMETERS.temperature == 0.0
    assert NORMALIZER_PARAMETERS.top_p == 0.1
    assert NORMALIZER_PARAMETERS.max_tokens == 2500
    assert CLASSIFIER_PARAMETERS.temperature == 0.0
    assert CLASSIFIER_PARAMETERS.top_p == 0.1
    assert IMPACT_PARAMETERS.temperature == 0.2
    assert IMPACT_PARAMETERS.top_p == 0.3
    assert IMPACT_PARAMETERS.max_tokens == 1800
