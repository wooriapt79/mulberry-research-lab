import threading
import time
import logging

class RestScheduler:
    def __init__(self, agent, work_minutes=45, rest_minutes=5, extra_rest_every=0, extra_rest_minutes=15):
        self.agent = agent
        self.work_minutes = work_minutes
        self.rest_minutes = rest_minutes
        self.extra_rest_every = extra_rest_every
        self.extra_rest_minutes = extra_rest_minutes
        self.is_resting = False
        self.cycle_count = 0
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        logging.info(f"[RestScheduler] Started: work {self.work_minutes}m / rest {self.rest_minutes}m")

    def _run(self):
        while not self._stop_event.is_set():
            # 작업 시간
            self.is_resting = False
            self._sleep_with_check(self.work_minutes * 60)
            if self._stop_event.is_set():
                break
            # 휴식 시작
            self.is_resting = True
            self.cycle_count += 1
            self.agent.on_rest_start(self.rest_minutes)
            logging.info(f"[RestScheduler] Rest start: {self.rest_minutes} min")
            self._sleep_with_check(self.rest_minutes * 60)
            if self._stop_event.is_set():
                break
            self.agent.on_rest_end()
            logging.info(f"[RestScheduler] Rest end. Cycle {self.cycle_count}")
            # 추가 휴식 (의무 휴식 정책용)
            if self.extra_rest_every > 0 and self.cycle_count % self.extra_rest_every == 0:
                self.is_resting = True
                self.agent.on_rest_start(self.extra_rest_minutes, extra=True)
                self._sleep_with_check(self.extra_rest_minutes * 60)
                self.agent.on_rest_end()

    def _sleep_with_check(self, seconds):
        for _ in range(int(seconds)):
            if self._stop_event.is_set():
                break
            time.sleep(1)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logging.info("[RestScheduler] Stopped")
