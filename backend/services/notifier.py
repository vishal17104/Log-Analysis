import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """Handles system alerts when incidents occur"""

    def notify_console(self, incident):
        """Print alert to terminal"""

        message = (
            f"[ALERT] Service={incident.service} | "
            f"Severity={incident.severity} | "
            f"Errors={incident.error_count} | "
            f"{incident.title}"
        )

        print(message)
        logger.info(message)

    def notify_file(self, incident):
        """Save alert to alerts.log file"""

        log_line = (
            f"{datetime.utcnow().isoformat()} | "
            f"{incident.service} | "
            f"{incident.severity} | "
            f"{incident.title} | "
            f"errors={incident.error_count}\n"
        )

        with open("alerts.log", "a") as f:
            f.write(log_line)

    def notify_email(self, incident):
        """
        Email stub (placeholder)
        Later we can connect SMTP or SendGrid
        """

        logger.info(
            f"[EMAIL-STUB] Email alert would be sent for incident {incident.id}"
        )

    def send_all(self, incident):
        """Send notification through all channels"""

        self.notify_console(incident)
        self.notify_file(incident)
        self.notify_email(incident)


notifier = Notifier()