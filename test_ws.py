# test_ws.py
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/logs"
    print(f"🔌 Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        response = await websocket.recv()
        print(f"✅ Connected: {response}")
        
        # Listen for logs
        print("📡 Waiting for logs (press Ctrl+C to stop)...")
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                data = json.loads(message)
                if data['type'] == 'log':
                    log = data['data']
                    print(f"[{log['level']}] {log['service']}: {log['message'][:50]}")
                else:
                    print(f"📨 {data}")
        except asyncio.TimeoutError:
            # No message received, continue waiting
            pass
        except KeyboardInterrupt:
            print("\n👋 Disconnecting...")

asyncio.run(test_websocket())