from config_agent.main import ConfigAgent

def test_pm_questions_field_exists():
    agent = ConfigAgent(mode="dev")
    report = agent.run()
    assert "pm_questions" in report
