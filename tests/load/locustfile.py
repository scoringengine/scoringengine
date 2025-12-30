"""
Locust load test for Scoring Engine WebSocket implementation

Install dependencies:
    pip install locust python-socketio

Run load test:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or with specific settings:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10

Access web UI at: http://localhost:8089
"""

import time
from locust import HttpUser, task, between, events
import socketio


class WebSocketClient:
    """Socket.IO client wrapper for Locust"""

    def __init__(self, base_url, request_event):
        self.base_url = base_url
        self.request_event = request_event
        self.sio = socketio.Client(reconnection=True)
        self.connected = False
        self.updates_received = 0

        # Setup event handlers
        @self.sio.on('connect')
        def on_connect():
            self.connected = True
            start_time = time.time()
            self.sio.emit('join_scoreboard')
            total_time = (time.time() - start_time) * 1000

            # Fire success event for Locust stats
            self.request_event.fire(
                request_type="WebSocket",
                name="connect",
                response_time=total_time,
                response_length=0,
                exception=None,
                context={}
            )

        @self.sio.on('disconnect')
        def on_disconnect():
            self.connected = False

        @self.sio.on('joined')
        def on_joined(data):
            # Track successful room join
            self.request_event.fire(
                request_type="WebSocket",
                name="join_room",
                response_time=0,
                response_length=len(str(data)),
                exception=None,
                context={}
            )

        @self.sio.on('scoreboard_update')
        def on_scoreboard_update(data):
            start_time = time.time()
            self.updates_received += 1
            total_time = (time.time() - start_time) * 1000

            # Track update receipt
            self.request_event.fire(
                request_type="WebSocket",
                name="scoreboard_update",
                response_time=total_time,
                response_length=len(str(data)),
                exception=None,
                context={}
            )

    def connect(self):
        """Connect to WebSocket server"""
        try:
            start_time = time.time()
            self.sio.connect(self.base_url, wait_timeout=10)
            total_time = (time.time() - start_time) * 1000
            return True
        except Exception as e:
            self.request_event.fire(
                request_type="WebSocket",
                name="connect",
                response_time=0,
                response_length=0,
                exception=e,
                context={}
            )
            return False

    def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.connected:
            self.sio.disconnect()


class ScoreboardViewer(HttpUser):
    """
    Simulates a scoreboard viewer with WebSocket connection
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Setup WebSocket connection when user starts"""
        self.ws_client = WebSocketClient(self.host, self.environment.events.request)
        self.ws_client.connect()

    def on_stop(self):
        """Cleanup WebSocket connection when user stops"""
        if hasattr(self, 'ws_client'):
            self.ws_client.disconnect()

    @task(3)
    def view_scoreboard(self):
        """Load scoreboard page"""
        self.client.get("/scoreboard")

    @task(2)
    def view_overview(self):
        """Load overview page"""
        self.client.get("/overview")

    @task(1)
    def get_bar_data(self):
        """Fetch bar chart data (initial load)"""
        self.client.get("/api/scoreboard/get_bar_data")

    @task(1)
    def get_line_data(self):
        """Fetch line chart data (initial load)"""
        self.client.get("/api/scoreboard/get_line_data")


class OverviewViewer(HttpUser):
    """
    Simulates an overview page viewer with WebSocket connection
    """
    wait_time = between(2, 8)

    def on_start(self):
        """Setup WebSocket connection"""
        self.ws_client = WebSocketClient(self.host, self.environment.events.request)
        self.ws_client.connect()

    def on_stop(self):
        """Cleanup WebSocket connection"""
        if hasattr(self, 'ws_client'):
            self.ws_client.disconnect()

    @task(5)
    def view_overview(self):
        """Load overview page"""
        self.client.get("/overview")

    @task(1)
    def get_overview_data(self):
        """Fetch overview table data"""
        self.client.get("/api/overview/get_data")

    @task(1)
    def get_round_data(self):
        """Fetch round header data"""
        self.client.get("/api/overview/get_round_data")


class PollingOnlyViewer(HttpUser):
    """
    Simulates old behavior: NO WebSocket, only polling
    Use this to compare performance with WebSocket implementation
    """
    wait_time = between(30, 30)  # Poll every 30 seconds like old implementation

    @task(1)
    def poll_scoreboard(self):
        """Simulate old 30-second polling behavior"""
        self.client.get("/api/scoreboard/get_bar_data")
        self.client.get("/api/scoreboard/get_line_data")


class APIOnlyTester(HttpUser):
    """
    Tests API endpoints only, no WebSocket
    """
    wait_time = between(1, 3)

    @task(2)
    def scoreboard_bar_data(self):
        self.client.get("/api/scoreboard/get_bar_data")

    @task(2)
    def scoreboard_line_data(self):
        self.client.get("/api/scoreboard/get_line_data")

    @task(1)
    def overview_data(self):
        self.client.get("/api/overview/get_data")

    @task(1)
    def overview_round_data(self):
        self.client.get("/api/overview/get_round_data")


# Stats reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*80)
    print("WebSocket Load Test Starting")
    print("="*80)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*80)
    print("WebSocket Load Test Completed")
    print("="*80)

    # Print stats
    stats = environment.stats
    print("\nRequest Statistics:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Total Failures: {stats.total.num_failures}")
    print(f"  Median Response Time: {stats.total.median_response_time}ms")
    print(f"  Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"  Min Response Time: {stats.total.min_response_time}ms")
    print(f"  Max Response Time: {stats.total.max_response_time}ms")
    print(f"  Requests/sec: {stats.total.total_rps:.2f}")

    # WebSocket specific stats
    ws_stats = [s for s in stats.entries.values() if s.method == "WebSocket"]
    if ws_stats:
        print("\nWebSocket Statistics:")
        for stat in ws_stats:
            print(f"  {stat.name}:")
            print(f"    Count: {stat.num_requests}")
            print(f"    Failures: {stat.num_failures}")
            print(f"    Avg Time: {stat.avg_response_time:.2f}ms")

    print("="*80 + "\n")
