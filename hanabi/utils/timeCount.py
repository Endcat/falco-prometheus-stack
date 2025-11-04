import time
from collections import deque

class EventCounter:
    def __init__(self):
        self.count = 0
        self.timestamps = deque()

    def on_event(self):
        now = int(time.time() * 1000)  # 当前时间戳（毫秒）
        self.timestamps.append(now)
        self.count += 1

        # 清理过期事件（超过1秒的）
        while self.timestamps and self.timestamps[0] < now - 1000:
            self.timestamps.popleft()
            self.count -= 1

    def get_rate(self):
        return self.count  # 当前一秒内的事件数
