--- Recorded at: 2026-04-02T16:13:06.541987 ---
class JangseungbaegiLibrary:
    def __init__(self, passport_service):
        self.modules = {'base_knowledge': 'Initial Data'}
        self.passport_service = passport_service

    def query(self, key, passport):
        if self.passport_service.check_permission(passport, 'library', key, 'read'):
            return self.modules.get(key, 'Standard Module')
        return 'Permission Denied'

class GhostArchive:
    def __init__(self, passport_service):
        self.records = []
        self.passport_service = passport_service

    def record(self, entry, passport):
        self.records.append(entry)
        return True
