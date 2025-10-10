import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Any
import io
import base64

from app_common.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending email reports."""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASS", "")
        self.smtp_from = os.getenv("SMTP_FROM", "noreply@magacin.com")
        self.use_tls = os.getenv("SMTP_TLS", "true").lower() == "true"
    
    async def send_report(
        self,
        recipients: List[str],
        report_content: Dict[str, Any],
        report_name: str,
        csv_data: str
    ) -> bool:
        """Send a KPI report via email."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"KPI Izvještaj - {report_name} - {datetime.now().strftime('%d.%m.%Y')}"
            
            # Create HTML body
            html_body = self._create_html_body(report_content, report_name)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Attach CSV file
            csv_attachment = MIMEBase('application', 'octet-stream')
            csv_attachment.set_payload(csv_data.encode('utf-8'))
            encoders.encode_base64(csv_attachment)
            csv_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename= "kpi-report-{datetime.now().strftime("%Y%m%d")}.csv"'
            )
            msg.attach(csv_attachment)
            
            # Send email
            await self._send_email(msg, recipients)
            
            logger.info(
                "EMAIL_REPORT_SENT",
                recipients=recipients,
                report_name=report_name,
                subject=msg['Subject']
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "EMAIL_REPORT_FAILED",
                recipients=recipients,
                report_name=report_name,
                error=str(e)
            )
            return False
    
    def _create_html_body(self, report_content: Dict[str, Any], report_name: str) -> str:
        """Create HTML email body with KPI summary and charts."""
        summary = report_content.get("summary", {})
        filters = report_content.get("filters", {})
        
        # Create chart placeholders (in production, you'd generate actual chart images)
        daily_chart = self._create_chart_placeholder("Dnevni trend", "line")
        workers_chart = self._create_chart_placeholder("Top radnici", "bar")
        manual_chart = self._create_chart_placeholder("Manual vs Skeniranje", "pie")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 2px solid #1890ff; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #1890ff; margin: 0; font-size: 28px; }}
                .header p {{ color: #666; margin: 5px 0 0 0; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .kpi-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; border-left: 4px solid #1890ff; }}
                .kpi-value {{ font-size: 32px; font-weight: bold; color: #1890ff; margin: 0; }}
                .kpi-label {{ color: #666; margin: 5px 0 0 0; font-size: 14px; }}
                .charts-section {{ margin: 30px 0; }}
                .chart-container {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 6px; }}
                .chart-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }}
                .chart-placeholder {{ height: 200px; background: #e9ecef; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #666; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                .filters {{ background: #f0f2f5; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
                .filters h3 {{ margin: 0 0 10px 0; color: #333; font-size: 16px; }}
                .filter-item {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>KPI Izvještaj</h1>
                    <p>{report_name} - {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                
                <div class="filters">
                    <h3>Filteri</h3>
                    <div class="filter-item"><strong>Period:</strong> {filters.get('period', 'N/A')}</div>
                    <div class="filter-item"><strong>Radnja:</strong> {filters.get('radnja', 'Sve')}</div>
                    <div class="filter-item"><strong>Radnik:</strong> {filters.get('radnik', 'Svi')}</div>
                </div>
                
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{summary.get('total_items', 0)}</div>
                        <div class="kpi-label">Ukupno stavki</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{summary.get('manual_percentage', 0):.1f}%</div>
                        <div class="kpi-label">Manual %</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{summary.get('avg_time_per_task', 0):.1f} min</div>
                        <div class="kpi-label">Prosječno vrijeme</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{summary.get('completed_tasks', 0)}</div>
                        <div class="kpi-label">Završeno zadataka</div>
                    </div>
                </div>
                
                <div class="charts-section">
                    <div class="chart-container">
                        <div class="chart-title">Dnevni trend obrade stavki</div>
                        <div class="chart-placeholder">
                            {daily_chart}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-title">Top 5 radnika po performansama</div>
                        <div class="chart-placeholder">
                            {workers_chart}
                        </div>
                    </div>
                    
                    <div class="chart-container">
                        <div class="chart-title">Distribucija: Manual vs Skeniranje</div>
                        <div class="chart-placeholder">
                            {manual_chart}
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Ovaj izvještaj je automatski generisan od strane Magacin Track sistema.</p>
                    <p>CSV prilog sadrži detaljne podatke u Pantheon MP formatu.</p>
                    <p>Generisano: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_chart_placeholder(self, title: str, chart_type: str) -> str:
        """Create a placeholder for chart (in production, generate actual chart image)."""
        return f"📊 {title} ({chart_type} chart would be displayed here)"
    
    async def _send_email(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP."""
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.smtp_from, recipients, text)
            server.quit()
            
            logger.info("EMAIL_SENT_SUCCESS", recipients=recipients)
            
        except Exception as e:
            logger.error("EMAIL_SEND_ERROR", error=str(e), recipients=recipients)
            raise


# Global email service instance
email_service = EmailService()


async def send_email_report(
    recipients: List[str],
    report_content: Dict[str, Any],
    report_name: str
) -> bool:
    """Send email report using the global email service."""
    csv_data = report_content.get("csv_data", "")
    return await email_service.send_report(recipients, report_content, report_name, csv_data)
