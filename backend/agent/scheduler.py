import time
from typing import List, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def start(self):
        self.scheduler.start()

    def scheduleJob(self, jobId: str, prompt: str, callback: Callable, runAt: str = None, intervalSeconds: int = None) -> Dict[str, Any]:
        #schedule task for a specific time or recurring interval
        if intervalSeconds:
            job = self.scheduler.add_job(
                callback,
                IntervalTrigger(seconds=intervalSeconds),
                args=[prompt],
                id=jobId,
                replace_existing=True
            )
        elif runAt:
            from datetime import datetime
            dt = datetime.fromisoformat(runAt)
            job = self.scheduler.add_job(
                callback,
                DateTrigger(run_date=dt),
                args=[prompt],
                id=jobId,
                replace_existing=True
            )
        else:
            #run immediately via asyncio
            import asyncio
            asyncio.create_task(callback(prompt))
            return {"id": jobId, "status": "executed_immediately"}

        info = {
            "id": jobId,
            "prompt": prompt,
            "nextRun": str(job.next_run_time),
            "type": "interval" if intervalSeconds else "date"
        }
        self._jobs[jobId] = info
        return info

    def deleteJob(self, jobId: str) -> bool:
        #remove active job from scheduler
        if jobId in self._jobs:
            self.scheduler.remove_job(jobId)
            del self._jobs[jobId]
            return True
        return False

    def getJobs(self) -> List[Dict[str, Any]]:
        #return list of active scheduled jobs
        return list(self._jobs.values())
