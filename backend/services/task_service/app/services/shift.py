"""Shift management service for team-based warehouse operations."""
from datetime import datetime, time, timedelta
from typing import Dict, Any, Optional
import pytz

from app_common.config import get_settings

settings = get_settings()


class ShiftConfig:
    """Configuration for warehouse shifts."""
    
    # Shift A timing
    SHIFT_A_START = time(8, 0)  # 08:00
    SHIFT_A_END = time(15, 0)   # 15:00
    SHIFT_A_BREAK_START = time(10, 0)   # 10:00
    SHIFT_A_BREAK_END = time(10, 30)    # 10:30
    
    # Shift B timing
    SHIFT_B_START = time(12, 0)  # 12:00
    SHIFT_B_END = time(19, 0)    # 19:00
    SHIFT_B_BREAK_START = time(14, 0)   # 14:00
    SHIFT_B_BREAK_END = time(14, 30)    # 14:30
    
    # Timezone
    TIMEZONE = pytz.timezone('Europe/Belgrade')
    
    @classmethod
    def get_shift_times(cls, shift: str) -> Dict[str, time]:
        """Get start, end, and break times for a shift."""
        if shift == 'A':
            return {
                'start': cls.SHIFT_A_START,
                'end': cls.SHIFT_A_END,
                'break_start': cls.SHIFT_A_BREAK_START,
                'break_end': cls.SHIFT_A_BREAK_END,
            }
        elif shift == 'B':
            return {
                'start': cls.SHIFT_B_START,
                'end': cls.SHIFT_B_END,
                'break_start': cls.SHIFT_B_BREAK_START,
                'break_end': cls.SHIFT_B_BREAK_END,
            }
        else:
            raise ValueError(f"Invalid shift: {shift}")


def get_current_time_in_timezone() -> datetime:
    """Get current time in Belgrade timezone."""
    return datetime.now(ShiftConfig.TIMEZONE)


def get_active_shift() -> Optional[str]:
    """Determine which shift is currently active (A, B, or None)."""
    now = get_current_time_in_timezone()
    current_time = now.time()
    
    # Check if Shift A is active
    if ShiftConfig.SHIFT_A_START <= current_time < ShiftConfig.SHIFT_A_END:
        return 'A'
    
    # Check if Shift B is active
    if ShiftConfig.SHIFT_B_START <= current_time < ShiftConfig.SHIFT_B_END:
        return 'B'
    
    return None


def is_on_break(shift: str) -> bool:
    """Check if the given shift is currently on break."""
    now = get_current_time_in_timezone()
    current_time = now.time()
    
    shift_times = ShiftConfig.get_shift_times(shift)
    return shift_times['break_start'] <= current_time < shift_times['break_end']


def get_shift_status(shift: str) -> Dict[str, Any]:
    """Get detailed status for a shift including countdown timers."""
    now = get_current_time_in_timezone()
    current_time = now.time()
    shift_times = ShiftConfig.get_shift_times(shift)
    
    # Determine shift status
    if current_time < shift_times['start']:
        status = 'not_started'
        next_event = 'shift_start'
        next_event_time = shift_times['start']
    elif current_time >= shift_times['end']:
        status = 'ended'
        next_event = None
        next_event_time = None
    elif shift_times['break_start'] <= current_time < shift_times['break_end']:
        status = 'on_break'
        next_event = 'break_end'
        next_event_time = shift_times['break_end']
    elif current_time < shift_times['break_start']:
        status = 'working'
        next_event = 'break_start'
        next_event_time = shift_times['break_start']
    else:  # After break, before end
        status = 'working'
        next_event = 'shift_end'
        next_event_time = shift_times['end']
    
    # Calculate countdown
    countdown_seconds = None
    if next_event_time:
        # Create datetime objects for today with the times
        today = now.date()
        next_datetime = ShiftConfig.TIMEZONE.localize(
            datetime.combine(today, next_event_time)
        )
        current_datetime = now
        
        if next_datetime > current_datetime:
            countdown_seconds = int((next_datetime - current_datetime).total_seconds())
        else:
            countdown_seconds = 0
    
    return {
        'shift': shift,
        'status': status,
        'next_event': next_event,
        'next_event_time': next_event_time.isoformat() if next_event_time else None,
        'countdown_seconds': countdown_seconds,
        'countdown_formatted': _format_countdown(countdown_seconds) if countdown_seconds else None,
        'shift_start': shift_times['start'].isoformat(),
        'shift_end': shift_times['end'].isoformat(),
        'break_start': shift_times['break_start'].isoformat(),
        'break_end': shift_times['break_end'].isoformat(),
    }


def _format_countdown(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_all_shifts_status() -> Dict[str, Any]:
    """Get status for all shifts."""
    active_shift = get_active_shift()
    
    return {
        'active_shift': active_shift,
        'shift_a_status': get_shift_status('A'),
        'shift_b_status': get_shift_status('B'),
        'current_time': get_current_time_in_timezone().isoformat(),
    }

