from googleplay_mcp.models import ListReviewsIn


def test_reviews_model_defaults():
    m = ListReviewsIn(package_name="com.example.app")
    assert m.max_results == 50
