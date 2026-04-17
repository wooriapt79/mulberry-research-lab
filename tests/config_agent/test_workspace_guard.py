from config_agent.main import ConfigAgent

def test_workspace_guard_runs():
    agent = ConfigAgent(mode="dev")
    report = agent.run()
    assert "workspace_issues" in report
