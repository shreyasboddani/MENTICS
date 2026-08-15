from app import build_strategy_article


def test_build_strategy_article_is_comprehensive_enough_for_sprint():
    article = build_strategy_article(
        "linear equation word problems",
        "You often set up the wrong equation before solving.",
    )

    content = article["content"]

    assert article["title"].startswith("Strategies for")
    assert "Step 1" in content
    assert "Common traps" in content
    assert "Worked example" in content
    assert "Quick self-check" in content
    assert len(content) > 1200
