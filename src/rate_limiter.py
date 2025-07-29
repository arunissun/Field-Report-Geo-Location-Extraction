import time
import logging
from datetime import datetime, timedelta
from typing import List


class RateLimiter:
    """Handle rate limiting for API calls"""

    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[datetime] = []
        self.logger = logging.getLogger(__name__)

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()

        # Remove requests older than 1 minute
        minute_ago = now - timedelta(minutes=1)
        self.request_times = [
            req_time for req_time in self.request_times
            if req_time > minute_ago
        ]

        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                self.logger.info(
                    f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                time.sleep(sleep_time)

        # Record this request
        self.request_times.append(now)

    def get_stats(self):
        """Get current rate limiting statistics"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            req for req in self.request_times if req > minute_ago
        ]

        return {
            'requests_last_minute': len(recent_requests),
            'requests_per_minute_limit': self.requests_per_minute,
            'remaining_capacity':
            self.requests_per_minute - len(recent_requests)
        }
