import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from app_common.logging import get_logger

logger = get_logger(__name__)


class ReportScheduler:
    """Scheduler for automated report sending."""
    
    def __init__(self):
        self.running = False
        self.schedules: Dict[str, Dict] = {}
        self.timezone = os.getenv("REPORT_CRON_TZ", "Europe/Belgrade")
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        logger.info("REPORT_SCHEDULER_STARTED", timezone=self.timezone)
        
        # Start the main scheduler loop
        asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("REPORT_SCHEDULER_STOPPED")
    
    async def add_schedule(self, schedule_id: str, schedule_data: Dict):
        """Add a new schedule to the scheduler."""
        self.schedules[schedule_id] = schedule_data
        logger.info("REPORT_SCHEDULE_ADDED", schedule_id=schedule_id)
    
    async def remove_schedule(self, schedule_id: str):
        """Remove a schedule from the scheduler."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            logger.info("REPORT_SCHEDULE_REMOVED", schedule_id=schedule_id)
    
    async def update_schedule(self, schedule_id: str, schedule_data: Dict):
        """Update an existing schedule."""
        self.schedules[schedule_id] = schedule_data
        logger.info("REPORT_SCHEDULE_UPDATED", schedule_id=schedule_id)
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for due reports."""
        while self.running:
            try:
                await self._check_schedules()
                # Check every minute
                await asyncio.sleep(60)
            except Exception as e:
                logger.error("REPORT_SCHEDULER_ERROR", error=str(e))
                await asyncio.sleep(60)
    
    async def _check_schedules(self):
        """Check all schedules and send reports that are due."""
        now = datetime.now()
        
        for schedule_id, schedule in self.schedules.items():
            if not schedule.get("enabled", False):
                continue
            
            if self._is_due(schedule, now):
                await self._send_scheduled_report(schedule_id, schedule)
    
    def _is_due(self, schedule: Dict, now: datetime) -> bool:
        """Check if a schedule is due to run."""
        frequency = schedule.get("frequency")
        time_hour = schedule.get("time_hour", 7)
        time_minute = schedule.get("time_minute", 0)
        last_sent = schedule.get("last_sent")
        
        # Create target time for today
        target_time = now.replace(hour=time_hour, minute=time_minute, second=0, microsecond=0)
        
        if frequency == "daily":
            # Send if target time has passed and we haven't sent today
            if now >= target_time:
                if last_sent is None or last_sent.date() < now.date():
                    return True
        
        elif frequency == "weekly":
            # Send on Monday at target time
            if now.weekday() == 0 and now >= target_time:  # Monday
                if last_sent is None or (now - last_sent).days >= 7:
                    return True
        
        elif frequency == "monthly":
            # Send on first day of month at target time
            if now.day == 1 and now >= target_time:
                if last_sent is None or last_sent.month != now.month:
                    return True
        
        return False
    
    async def _send_scheduled_report(self, schedule_id: str, schedule: Dict):
        """Send a scheduled report."""
        try:
            logger.info("REPORT_SCHEDULED_SEND_START", schedule_id=schedule_id)
            
            # Import here to avoid circular imports
            from ..routers.reports import send_report
            
            recipients = schedule.get("recipients", [])
            filters = schedule.get("filters", {})
            
            await send_report(schedule_id, recipients, filters, manual=False)
            
            # Update last sent time
            schedule["last_sent"] = datetime.utcnow()
            
            logger.info("REPORT_SCHEDULED_SEND_SUCCESS", schedule_id=schedule_id)
            
        except Exception as e:
            logger.error("REPORT_SCHEDULED_SEND_FAILED", schedule_id=schedule_id, error=str(e))


# Global scheduler instance
scheduler = ReportScheduler()


async def start_scheduler():
    """Start the global scheduler."""
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    await scheduler.stop()


async def add_schedule_to_scheduler(schedule_id: str, schedule_data: Dict):
    """Add a schedule to the global scheduler."""
    await scheduler.add_schedule(schedule_id, schedule_data)


async def remove_schedule_from_scheduler(schedule_id: str):
    """Remove a schedule from the global scheduler."""
    await scheduler.remove_schedule(schedule_id)


async def update_schedule_in_scheduler(schedule_id: str, schedule_data: Dict):
    """Update a schedule in the global scheduler."""
    await scheduler.update_schedule(schedule_id, schedule_data)
