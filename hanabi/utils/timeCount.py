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

        # 清理过期事件（超过10秒的）
        while self.timestamps and now - self.timestamps[0] > 1000 * 10:
            self.timestamps.popleft()
            self.count -= 1

    def get_rate(self):
        return self.count  # 当前10秒内的事件数
