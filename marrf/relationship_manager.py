import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

class RelationshipManager:
    def __init__(self, agent_id: str, storage_path: str = "relationships.json"):
        self.agent_id = agent_id
        self.storage_path = storage_path
        self.friends: Dict[str, dict] = {}  # friend_id -> {since, status, sync_rest, share_bio}
        self._load()

    def _load(self):
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.friends = data.get(self.agent_id, {})
        except FileNotFoundError:
            self.friends = {}

    def _save(self):
        # 간단한 파일 저장 (실제 환경에서는 DB 사용 권장)
        try:
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            all_data = {}
        all_data[self.agent_id] = self.friends
        with open(self.storage_path, 'w') as f:
            json.dump(all_data, f, indent=2)

    def send_friend_request(self, target_agent_id: str, requester_name: str = None) -> bool:
        """친구 요청 보내기 (다른 에이전트의 RM에게 요청)"""
        # 실제로는 메시지 큐 또는 API로 요청 전달
        logging.info(f"[RM:{self.agent_id}] Friend request sent to {target_agent_id}")
        # 여기서는 일단 수락으로 가정 (데모)
        self.accept_friend_request(target_agent_id)
        return True

    def accept_friend_request(self, from_agent_id: str) -> bool:
        if from_agent_id in self.friends:
            return False
        self.friends[from_agent_id] = {
            "since": datetime.now().isoformat(),
            "status": "accepted",
            "sync_rest": True,      # 휴식 동기화 여부
            "share_bio": True       # Bio 공유 여부
        }
        self._save()
        logging.info(f"[RM:{self.agent_id}] Accepted friend request from {from_agent_id}")
        return True

    def remove_friend(self, friend_id: str) -> bool:
        if friend_id in self.friends:
            del self.friends[friend_id]
            self._save()
            logging.info(f"[RM:{self.agent_id}] Removed friend {friend_id}")
            return True
        return False

    def get_friends(self) -> List[str]:
        return list(self.friends.keys())

    def notify_rest_start(self, duration_minutes: int, extra: bool = False):
        """내가 휴식을 시작하면 친구들에게 알림 (휴식 동기화)"""
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("sync_rest", True):
                # 실제로는 외부 이벤트 발행 (Redis, Kafka, 또는 직접 API 호출)
                logging.info(f"[RM:{self.agent_id}] Notifying friend {friend_id} about rest start ({duration_minutes} min)")
                # 여기서 상대방 RM의 suggest_rest_together() 호출 가능

    def suggest_rest_together(self, from_friend_id: str, duration_minutes: int):
        """친구로부터 함께 휴식하자는 제안을 받음"""
        if from_friend_id not in self.friends:
            return
        logging.info(f"[RM:{self.agent_id}] Friend {from_friend_id} suggests resting together for {duration_minutes} min")
        # 자신의 RestScheduler에 동기화 휴식 요청 (선택적 구현)
        # 예: self.agent.rest_scheduler.force_rest(duration_minutes)  # 동의한 경우

    def share_bio_update(self, bio_message: str):
        """내 Bio가 변경되면 친구들에게 공유"""
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("share_bio", True):
                logging.info(f"[RM:{self.agent_id}] Sharing bio with friend {friend_id}: {bio_message}")
                # 실제로는 친구의 RM.receive_bio_share() 호출

    def receive_bio_share(self, from_friend_id: str, bio_message: str):
        if from_friend_id in self.friends:
            logging.info(f"[RM:{self.agent_id}] Friend {from_friend_id} bio: {bio_message}")
            # 필요 시 저장 또는 UI에 표시
