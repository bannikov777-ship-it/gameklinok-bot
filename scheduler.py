# scheduler.py
import asyncio
import time
import heapq
from typing import Callable, Any

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.counter = 0
        self.running = True

    async def run(self):
        print("🔄 [SCHEDULER] ЗАПУЩЕН И РАБОТАЕТ")
        while self.running:
            now = time.time()
            if self.tasks:
                print(f"🔍 [SCHEDULER] В очереди {len(self.tasks)} задач, ближайшая через {self.tasks[0][0] - now:.1f} сек")
            while self.tasks and self.tasks[0][0] <= now:
                _, _, callback, args, kwargs = heapq.heappop(self.tasks)
                try:
                    print(f"⏳ [SCHEDULER] Выполняется задача: {callback.__name__}")
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(*args, **kwargs))
                    else:
                        await asyncio.to_thread(callback, *args, **kwargs)
                except Exception as e:
                    print(f"❌ [SCHEDULER] Ошибка выполнения задачи: {e}")
                    import traceback
                    traceback.print_exc()
            await asyncio.sleep(0.5)

    def schedule(self, delay_seconds: float, callback: Callable, *args, **kwargs):
        self.counter += 1
        task_id = self.counter
        execute_at = time.time() + delay_seconds
        heapq.heappush(self.tasks, (execute_at, task_id, callback, args, kwargs))
        print(f"📅 [SCHEDULER] Запланирована задача #{task_id} через {delay_seconds} сек: {callback.__name__}")
        return task_id

    def cancel(self, task_id):
        self.tasks = [(t, tid, cb, a, k) for t, tid, cb, a, k in self.tasks if tid != task_id]
        heapq.heapify(self.tasks)
        print(f"❌ [SCHEDULER] Задача #{task_id} отменена")

    def stop(self):
        self.running = False
        print("🛑 [SCHEDULER] Остановлен")

scheduler = Scheduler()