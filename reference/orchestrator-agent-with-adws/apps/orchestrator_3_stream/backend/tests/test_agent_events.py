#!/usr/bin/env python3
"""
Test script to verify agent events are broadcast via WebSocket in real-time
"""

import asyncio
import json
from datetime import datetime

import websockets


async def listen_for_agent_events():
    """
    Connect to WebSocket and listen for agent_log events
    """
    uri = "ws://127.0.0.1:9403/ws"

    print(f"🔌 Connecting to WebSocket at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            print("📡 Listening for agent events...")
            print("-" * 50)

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Filter for agent_log events
                    if data.get("type") == "agent_log":
                        log = data.get("log", {})
                        print(f"\n🎯 AGENT EVENT RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
                        print(f"   Type: {log.get('event_type')}")
                        print(f"   Category: {log.get('event_category')}")
                        print(f"   Agent ID: {log.get('agent_id')}")
                        print(f"   Content: {log.get('content', 'N/A')[:100]}")

                        # Special handling for different event types
                        if log.get('event_type') == 'TextBlock':
                            print(f"   📝 Agent Response: {log.get('content', '')[:200]}")
                        elif log.get('event_type') == 'ThinkingBlock':
                            print(f"   🤔 Agent Thinking...")
                        elif log.get('event_type') == 'ToolUseBlock':
                            payload = log.get('payload', {})
                            print(f"   🔧 Tool Use: {payload.get('tool_name', 'unknown')}")
                        elif log.get('event_type') in ['PreToolUse', 'PostToolUse']:
                            payload = log.get('payload', {})
                            print(f"   🛠️ Hook: {payload.get('tool_name', 'unknown')}")

                    elif data.get("type") == "agent_status_changed":
                        print(f"\n📊 Agent Status Changed: {data.get('old_status')} → {data.get('new_status')}")

                    elif data.get("type") == "agent_created":
                        agent = data.get('agent', {})
                        print(f"\n🆕 Agent Created: {agent.get('name')} (ID: {agent.get('id')})")

                    # Ignore connection established and heartbeat messages
                    elif data.get("type") not in ["connection_established", "heartbeat"]:
                        print(f"\n📨 Other event: {data.get('type')}")

                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ WebSocket connection closed")
                    break
                except json.JSONDecodeError as e:
                    print(f"\n⚠️ Failed to parse message: {e}")
                except Exception as e:
                    print(f"\n⚠️ Error: {e}")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\n💡 Make sure the backend is running with:")
        print("   cd apps/orchestrator_3_stream && ./start_be.sh")


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT EVENT WEBSOCKET LISTENER")
    print("=" * 60)
    print("\nThis script listens for real-time agent events via WebSocket.")
    print("To test:")
    print("1. Make sure the backend is running (./start_be.sh)")
    print("2. Open the frontend and command an agent")
    print("3. Watch events appear here in real-time!\n")

    try:
        asyncio.run(listen_for_agent_events())
    except KeyboardInterrupt:
        print("\n\n👋 Listener stopped")