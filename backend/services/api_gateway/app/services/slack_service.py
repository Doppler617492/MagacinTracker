import os
import json
from datetime import datetime
from typing import List, Dict, Any
import aiohttp

from app_common.logging import get_logger

logger = get_logger(__name__)


class SlackService:
    """Service for sending Slack notifications."""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.channel = os.getenv("SLACK_CHANNEL", "#magacin-reports")
        self.username = os.getenv("SLACK_USERNAME", "Magacin Bot")
        self.icon_emoji = os.getenv("SLACK_ICON_EMOJI", ":chart_with_upwards_trend:")
    
    async def send_report(
        self,
        recipients: List[str],
        report_content: Dict[str, Any],
        report_name: str,
        csv_data: str
    ) -> bool:
        """Send a KPI report via Slack."""
        try:
            if not self.webhook_url:
                logger.warning("SLACK_WEBHOOK_URL not configured")
                return False
            
            # Create Slack message
            message = self._create_slack_message(report_content, report_name, csv_data)
            
            # Send to Slack
            await self._send_slack_message(message, recipients)
            
            logger.info(
                "SLACK_REPORT_SENT",
                recipients=recipients,
                report_name=report_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "SLACK_REPORT_FAILED",
                recipients=recipients,
                report_name=report_name,
                error=str(e)
            )
            return False
    
    def _create_slack_message(
        self,
        report_content: Dict[str, Any],
        report_name: str,
        csv_data: str
    ) -> Dict[str, Any]:
        """Create Slack message with KPI summary and CSV data."""
        summary = report_content.get("summary", {})
        filters = report_content.get("filters", {})
        
        # Create KPI summary text
        kpi_text = f"""
📊 *KPI Izvještaj - {report_name}*
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}

*Ključni pokazatelji:*
• Ukupno stavki: {summary.get('total_items', 0):,}
• Manual %: {summary.get('manual_percentage', 0):.1f}%
• Prosječno vrijeme: {summary.get('avg_time_per_task', 0):.1f} min
• Završeno zadataka: {summary.get('completed_tasks', 0)}

*Filteri:*
• Period: {filters.get('period', 'N/A')}
• Radnja: {filters.get('radnja', 'Sve')}
• Radnik: {filters.get('radnik', 'Svi')}
        """.strip()
        
        # Create top workers section
        top_workers = report_content.get("charts", {}).get("top_workers", [])
        if top_workers:
            workers_text = "\n*Top radnici:*\n"
            for i, worker in enumerate(top_workers[:3], 1):
                workers_text += f"{i}. {worker.get('worker_name', 'N/A')}: {worker.get('completed_tasks', 0)} zadataka\n"
            kpi_text += workers_text
        
        # Create manual vs scanning section
        manual_data = report_content.get("charts", {}).get("manual_completion", [])
        if manual_data:
            scanned = next((item for item in manual_data if item.get('type') == 'scanned'), {}).get('value', 0)
            manual = next((item for item in manual_data if item.get('type') == 'manual'), {}).get('value', 0)
            total = scanned + manual
            
            if total > 0:
                scanned_pct = (scanned / total) * 100
                manual_pct = (manual / total) * 100
                kpi_text += f"\n*Distribucija:*\n• Skenirano: {scanned} ({scanned_pct:.1f}%)\n• Ručno: {manual} ({manual_pct:.1f}%)"
        
        # Create CSV data section (truncated for Slack)
        csv_lines = csv_data.split('\n')
        csv_preview = '\n'.join(csv_lines[:10])  # First 10 lines
        if len(csv_lines) > 10:
            csv_preview += f"\n... (ukupno {len(csv_lines)} linija)"
        
        # Create Slack message
        message = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "text": kpi_text,
            "attachments": [
                {
                    "color": "#1890ff",
                    "title": "CSV Podaci (Pantheon MP format)",
                    "text": f"```\n{csv_preview}\n```",
                    "footer": "Magacin Track System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        return message
    
    async def _send_slack_message(self, message: Dict[str, Any], recipients: List[str]):
        """Send message to Slack via webhook."""
        try:
            async with aiohttp.ClientSession() as session:
                # Override channel if recipients are specified
                if recipients:
                    # Assume recipients are channel names (e.g., #channel-name)
                    for recipient in recipients:
                        if recipient.startswith('#'):
                            message_copy = message.copy()
                            message_copy["channel"] = recipient
                            
                            async with session.post(
                                self.webhook_url,
                                json=message_copy,
                                headers={"Content-Type": "application/json"}
                            ) as response:
                                if response.status == 200:
                                    logger.info("SLACK_MESSAGE_SENT", channel=recipient)
                                else:
                                    logger.error("SLACK_MESSAGE_FAILED", channel=recipient, status=response.status)
                else:
                    # Send to default channel
                    async with session.post(
                        self.webhook_url,
                        json=message,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            logger.info("SLACK_MESSAGE_SENT", channel=self.channel)
                        else:
                            logger.error("SLACK_MESSAGE_FAILED", channel=self.channel, status=response.status)
            
        except Exception as e:
            logger.error("SLACK_SEND_ERROR", error=str(e))
            raise


# Global Slack service instance
slack_service = SlackService()


async def send_slack_report(
    recipients: List[str],
    report_content: Dict[str, Any],
    report_name: str
) -> bool:
    """Send Slack report using the global Slack service."""
    csv_data = report_content.get("csv_data", "")
    return await slack_service.send_report(recipients, report_content, report_name, csv_data)
