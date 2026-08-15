from app import build_strategy_article


def test_build_strategy_article_is_comprehensive_enough_for_sprint():
    article = build_strategy_article(
        "linear equation word problems",
        "You often set up the wrong equation before solving.",
    )

    content = article["content"]

    assert article["title"].startswith("Strategies for")
    # Check for educational content section
    assert "What you need to know for the quiz" in content
    assert "Essential concepts and skills for this topic" in content
    assert "Worked examples with" in content
    assert "Common" in content and ("misconception" in content.lower() or "trap" in content.lower())
    # Check for quiz strategies section
    assert "Quiz and sprint strategies" in content or "strategy" in content.lower()
    assert "Decision checklist" in content
    assert len(content) > 2000


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
    # Check for comprehensive study guide structure
    assert "what you need to know for the quiz" in content
    assert "worked examples" in content
