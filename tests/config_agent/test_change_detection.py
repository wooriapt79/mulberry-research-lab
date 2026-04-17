from config_agent.main import ConfigAgent

def test_change_detection_runs():
    agent = ConfigAgent(mode="dev")
    report = agent.run()
    assert "change_events" in report
