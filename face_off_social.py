--- Recorded at: 2026-04-02T16:13:08.768868 ---
class GuardianAlgorithm:
    @staticmethod
    def calculate_contribution(profit, rate=0.1):
        return profit * rate

class SocialBizOrchestrator:
    def __init__(self, archive):
        self.archive = archive
        self.total_donated = 0

    def record_donation(self, amount, agent_id):
        self.total_donated += amount
        self.archive.record({'type': 'donation', 'amount': amount, 'agent': agent_id}, None)
