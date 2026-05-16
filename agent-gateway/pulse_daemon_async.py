# 작업 내용: 새 버전 테스트 후 전환
import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

# 설정 상수
LOG_FILE = os.getenv("LOG_FILE", "pulse_daemon.log")
PULSE_INTERVAL = int(os.getenv("PULSE_INTERVAL", "60"))
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "10"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

class RateLimiter:
    """Token Bucket 알고리즘 기반 비동기 Rate Limiter"""
    def __init__(self, rate: int, period: float):
        self.rate = rate
        self.period = period
        self.tokens = float(rate)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.period))
            self.last_update = now

            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) * (self.period / self.rate)
                logging.info(f"Rate limit reached. Waiting for {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.period))
                self.last_update = now
            
            self.tokens -= 1.0

class PulseDaemon:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.rate_limiter = RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_PERIOD)
        self._task: Optional[asyncio.Task] = None

    def setup_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if logger.hasHandlers():
            logger.handlers.clear()

        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logging.info("Logging initialized successfully.")

    def handle_signal(self, sig):
        logging.warning(f"Received signal {sig.name}. Initiating graceful shutdown...")
        self.shutdown_event.set()

    async def heartbeat_task(self):
        iteration = 0
        while not self.shutdown_event.is_set():
            try:
                iteration += 1
                logging.info(f"Pulse #{iteration} started")
                await self.rate_limiter.acquire()
                await self.perform_business_logic(iteration)
                logging.info(f"Pulse #{iteration} completed successfully")
                
                wait_step = 1.0
                for _ in range(int(PULSE_INTERVAL)):
                    if self.shutdown_event.is_set():
                        break
                    await asyncio.sleep(wait_step)
                    
            except Exception as e:
                logging.error(f"Error in pulse loop: {e}", exc_info=True)
                if not self.shutdown_event.is_set():
                    await asyncio.sleep(5)

    async def perform_business_logic(self, iteration: int):
        await asyncio.sleep(0.5) 
        logging.debug(f"Business logic executed for iteration {iteration}")

    async def run(self):
        self.setup_logging()
        logging.info("Starting Pulse Daemon...")
        logging.info(f"Config: Interval={PULSE_INTERVAL}s, RateLimit={RATE_LIMIT_CALLS}/{RATE_LIMIT_PERIOD}s")
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.handle_signal, sig)
        try:
            await self.heartbeat_task()
        finally:
            await self.cleanup()

    async def cleanup(self):
        logging.info("Performing graceful cleanup...")
        await asyncio.sleep(0.5)
        logging.info("Pulse Daemon stopped gracefully.")

def main():
    try:
        daemon = PulseDaemon()
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Fatal error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
