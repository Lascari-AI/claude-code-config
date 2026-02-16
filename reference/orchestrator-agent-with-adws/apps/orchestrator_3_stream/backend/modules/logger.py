#!/usr/bin/env python3
"""
Comprehensive Logging Module
Logs to both console and hourly rotating log files for e2e debugging
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Rich console for formatted output
console = Console()


class HourlyRotatingFileHandler(logging.Handler):
    """Custom handler that rotates log files every hour"""

    def __init__(self, logs_dir: Path):
        super().__init__()
        self.logs_dir = logs_dir
        self.current_file = None
        self.current_hour = None

    def emit(self, record):
        """Emit a record to the appropriate hourly log file"""
        try:
            # Get current hour timestamp
            now = datetime.now()
            hour_key = now.strftime("%Y-%m-%d_%H")

            # Rotate file if hour changed
            if hour_key != self.current_hour:
                if self.current_file:
                    self.current_file.close()

                log_file_path = self.logs_dir / f"{hour_key}.log"
                self.current_file = open(log_file_path, "a", encoding="utf-8")
                self.current_hour = hour_key

                # Write header for new file
                self.current_file.write(f"\n{'='*80}\n")
                self.current_file.write(
                    f"Log Session Started: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                self.current_file.write(f"{'='*80}\n\n")

            # Write log message
            log_entry = self.format(record)
            self.current_file.write(log_entry + "\n")
            self.current_file.flush()

        except Exception as e:
            print(f"Error writing to log file: {e}", file=sys.stderr)

    def close(self):
        """Close current log file"""
        if self.current_file:
            self.current_file.close()
        super().close()


class OrchestratorLogger:
    """
    Centralized logger for the orchestrator backend
    Logs to both console (with Rich formatting) and hourly rotating files
    """

    def __init__(self, name: str = "orchestrator"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # Don't propagate to root logger

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add Rich console handler
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Add hourly rotating file handler
        file_handler = HourlyRotatingFileHandler(LOGS_DIR)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"[cyan]{message}[/cyan]", **kwargs)

    def success(self, message: str, **kwargs):
        """Log success message"""
        self.logger.info(f"[green]✅ {message}[/green]", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"[yellow]⚠️  {message}[/yellow]", **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(f"[red]❌ {message}[/red]", **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(f"[bold red]🔥 {message}[/bold red]", **kwargs)

    def panel(self, message: str, title: str = "", style: str = "cyan", expand: bool = True):
        """Log a Rich panel (console only, file gets plain text)"""
        # Log to console with Rich panel
        console.print(Panel(message, title=title, border_style=style, expand=expand))

        # Log to file as plain text
        plain_message = f"{title}: {message}" if title else message
        self.logger.info(f"[PANEL] {plain_message}", extra={"markup": False})

    def section(self, title: str, style: str = "bold cyan"):
        """Log a section header"""
        separator = "=" * 80
        self.panel(f"[{style}]{title}[/{style}]", title="", style=style.split()[-1])
        self.logger.info(f"\n{separator}\n{title}\n{separator}", extra={"markup": False})

    def websocket_event(self, event_type: str, data: dict):
        """Log WebSocket events"""
        self.info(f"📡 WebSocket Event: {event_type} | Data: {data}")

    def agent_event(self, agent_id: str, event_type: str, message: str):
        """Log agent-specific events"""
        self.info(f"🤖 Agent-{agent_id} | {event_type}: {message}")

    def chat_event(self, orchestrator_id: str, message: str, sender: str = "orchestrator"):
        """Log chat interaction events"""
        truncated_msg = message[:100] + "..." if len(message) > 100 else message
        self.info(f"💬 Chat [{orchestrator_id}] {sender.upper()}: {truncated_msg}")

    def http_request(self, method: str, path: str, status: int = None):
        """Log HTTP requests"""
        status_text = f"[{status}]" if status else ""
        self.info(f"🌐 {method} {path} {status_text}")

    def startup(self, config: dict):
        """Log startup information"""
        self.section("🚀 ORCHESTRATOR BACKEND STARTING", "bold cyan")
        for key, value in config.items():
            self.info(f"  {key}: {value}")

    def shutdown(self):
        """Log shutdown"""
        self.section("👋 ORCHESTRATOR BACKEND SHUTTING DOWN", "bold yellow")


# Global logger instance
logger = OrchestratorLogger()


def get_logger() -> OrchestratorLogger:
    """Get the global logger instance"""
    return logger
