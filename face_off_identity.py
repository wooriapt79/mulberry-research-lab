--- Recorded at: 2026-04-02T16:13:05.368080 ---
import uuid
from datetime import datetime, timedelta

class AP2Mandate:
    def __init__(self, task, context, start_time, duration_minutes, payment_info=None):
        self.task = task
        self.context = context
        self.start_time = start_time
        self.duration = timedelta(minutes=duration_minutes)
        self.payment_info = payment_info or {}

class AgentPassport:
    def __init__(self, agent_type, passport_id=None, expiry_date=None, credentials=None):
        self.passport_id = passport_id if passport_id else f'did:agent:{uuid.uuid4().hex[:8]}'
        self.agent_type = agent_type
        self.status = 'active'
        self.expiry_date = expiry_date
        self.credentials = credentials or {}

    def is_valid(self):
        if self.status != 'active': return False
        if self.expiry_date and datetime.now() > self.expiry_date: return False
        return True
