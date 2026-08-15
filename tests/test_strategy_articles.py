from app import build_strategy_article


def test_build_strategy_article_is_comprehensive_enough_for_sprint():
    article = build_strategy_article(
        "linear equation word problems",
        "You often set up the wrong equation before solving.",
    )

    content = article["content"]

    assert article["title"].startswith("Strategies for")
    assert "Step 1" in content
    assert "What to look for in this skill" in content
    assert "Worked example" in content
    assert "Quick drill for the sprint or quiz" in content
    assert "Final takeaway" in content
    assert len(content) > 1800


def test_build_strategy_article_uses_the_task_specific_skill():
    article = build_strategy_article(
        "quadratic graph transformations",
        "You mix up horizontal and vertical shifts.",
        "Practice Sprint: Graphing quadratic shifts in vertex form",
    )
    content = article["content"].lower()

    assert "graphing quadratic shifts" in article["title"].lower()
    assert "vertex form" in content
    assert "horizontal" in content
    assert "vertical" in content


def test_build_strategy_article_ignores_resource_link_text():
    article = build_strategy_article(
        "reading and writing",
        "You need stronger inference and vocabulary strategy work.",
        "Read the official guide on [Digital SAT Reading and Writing Module Strategies](https://example.com) to refine pacing for inference and vocabulary questions.",
    )
    content = article["content"].lower()

    assert "official guide" not in content
    assert "inference" in content
    assert "vocabulary" in content
    assert "digital sat reading and writing module strategies" not in article["title"].lower()
    assert "what to look for in this skill" in content
