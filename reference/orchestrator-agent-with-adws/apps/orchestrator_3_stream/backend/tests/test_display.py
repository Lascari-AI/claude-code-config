#!/usr/bin/env python3
"""
Test script to verify agent names and tool info are displayed correctly
"""

import asyncio
import json
from datetime import datetime

import websockets
from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()

async def monitor_agent_events():
    """Monitor WebSocket for agent events with name and tool display"""
    uri = "ws://127.0.0.1:9403/ws"

    try:
        async with websockets.connect(uri) as websocket:
            console.print("[green]✅ Connected to WebSocket[/green]\n")

            # Create live updating table
            table = Table(title="Agent Event Stream", show_header=True, header_style="bold magenta")
            table.add_column("Time", style="cyan", width=10)
            table.add_column("Agent", style="green", width=15)
            table.add_column("Type", style="yellow", width=15)
            table.add_column("Content", style="white", width=50)

            with Live(table, refresh_per_second=2) as live:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)

                        # Process agent_log events only
                        if data.get("type") == "agent_log":
                            log = data.get("log", {})

                            # Extract fields
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            agent_name = log.get("agent_name", f"ID:{log.get('agent_id', 'unknown')[-4:]}")
                            event_type = log.get("event_type", "unknown")

                            # Extract content based on event type
                            if "Tool" in event_type:
                                tool_name = log.get("payload", {}).get("tool_name", "unknown")
                                content = f"🔧 {tool_name}"
                            else:
                                content = (log.get("summary") or log.get("content") or "—")[:50]

                            # Add row and maintain table size
                            table.add_row(timestamp, agent_name, event_type, content)
                            if len(table.rows) > 20:
                                table.rows = table.rows[-20:]

                            live.update(table)

                    except websockets.exceptions.ConnectionClosed:
                        console.print("\n[red]Connection closed[/red]")
                        break
                    except json.JSONDecodeError:
                        pass  # Skip malformed messages

    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        console.print("[yellow]Ensure backend is running: ./start_be.sh[/yellow]")

if __name__ == "__main__":
    console.print("=" * 60)
    console.print("[bold cyan]AGENT NAME & TOOL DISPLAY TEST[/bold cyan]")
    console.print("=" * 60)
    console.print("\nMonitoring agent events for names and tool usage...\n")

    try:
        asyncio.run(monitor_agent_events())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test stopped[/yellow]")