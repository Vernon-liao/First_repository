from src.release_readiness import CampaignSimulator, build_demo_campaign_save


def test_e2e_from_new_campaign_to_chapter_1_settlement():
    simulator = CampaignSimulator(campaign_id="campaign-e2e")
    result = simulator.run_chapter_flow(chapter_id="chapter-1")

    assert result.chapter_settled is True
    assert result.rollback_applied is False
    assert result.events[0] == "CAMPAIGN_CREATED"
    assert result.events[-1] == "CHAPTER_1_SETTLED"
    assert result.fallback_summary == {
        "narrative_fallback": False,
        "image_fallback": False,
        "save_recovery": False,
    }


def test_failure_drills_timeout_image_fail_and_save_interruption_have_fallbacks():
    simulator = CampaignSimulator(campaign_id="campaign-failure-drill")
    result = simulator.run_chapter_flow(
        chapter_id="chapter-1",
        narrative_mode="timeout",
        image_mode="failure",
        save_mode="interrupted",
    )

    assert result.chapter_settled is True
    assert result.rollback_applied is True
    assert "ROLLBACK_PERFORMED" in result.events
    assert result.fallback_summary == {
        "narrative_fallback": True,
        "image_fallback": True,
        "save_recovery": True,
    }
    assert any(log["detail"] == "narrative_timeout_fallback_template" for log in result.logs)
    assert any(log["detail"] == "image_placeholder_uri" for log in result.logs)
    assert any(log["detail"] == "save_interrupted_rollback_to_last_checkpoint" for log in result.logs)


def test_acceptance_metrics_contains_functional_log_and_performance_dimensions():
    simulator = CampaignSimulator(campaign_id="campaign-acceptance")
    result = simulator.run_chapter_flow(chapter_id="chapter-1")

    assert len(result.logs) >= 3
    assert result.performance["first_screen_ms"] >= 0
    assert result.performance["single_step_response_ms"] >= 0


def test_demo_campaign_save_is_settled_and_reusable():
    save = build_demo_campaign_save()

    assert save["campaign_id"] == "demo-campaign-v0.1"
    assert save["chapter_settled"] is True
    assert save["version"] == "v0.1"
    assert save["events"][-1] == "CHAPTER_1_SETTLED"
