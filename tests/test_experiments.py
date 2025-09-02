from googleplay_mcp.models import ExperimentCreateIn


def test_experiment_model_defaults():
    m = ExperimentCreateIn(package_name="com.example.app", experiment_id="exp1", variant_id="v1")
    assert m.traffic_percent == 50
