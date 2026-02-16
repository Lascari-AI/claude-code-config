#!/usr/bin/env python3
"""
Raw WebSocket test to see exactly what's being broadcast
"""

import asyncio
import json
from datetime import datetime

import websockets


async def log_all_messages():
    """Log all WebSocket messages to see what's being sent"""
    uri = "ws://127.0.0.1:9403/ws"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Logging all messages...\n")
            print("-" * 80)

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    msg_type = data.get("type", "unknown")
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Log everything except heartbeats and connection messages
                    if msg_type not in ["heartbeat", "connection_established"]:
                        print(f"\n[{timestamp}] Type: {msg_type}")

                        # Special handling for agent_log
                        if msg_type == "agent_log":
                            log = data.get("log", {})
                            print(f"  Agent ID: {log.get('agent_id', 'N/A')}")
                            print(f"  Agent Name: {log.get('agent_name', 'MISSING!')}")
                            print(f"  Event Type: {log.get('event_type', 'N/A')}")
                            print(f"  Event Category: {log.get('event_category', 'N/A')}")
                            print(f"  Content: {str(log.get('content', 'N/A'))[:100]}")
                            if log.get('payload', {}).get('tool_name'):
                                print(f"  Tool: {log['payload']['tool_name']}")

                        # Log other message types
                        else:
                            print(f"  Data: {json.dumps(data, indent=2)[:500]}")

                        print("-" * 80)

                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ Connection closed")
                    break
                except json.JSONDecodeError as e:
                    print(f"Failed to parse: {e}")
                except Exception as e:
                    print(f"Error: {e}")

    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Make sure backend is running: ./start_be.sh")

if __name__ == "__main__":
    print("=" * 80)
    print("RAW WEBSOCKET MESSAGE LOGGER")
    print("=" * 80)
    print("\nThis will log ALL WebSocket messages to debug what's being sent.\n")

    try:
        asyncio.run(log_all_messages())
    except KeyboardInterrupt:
        print("\n\nStopped")