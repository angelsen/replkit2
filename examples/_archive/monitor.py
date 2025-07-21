#!/usr/bin/env python3
"""
System monitor example showcasing TextKit's data visualization.

Run interactively:
    uv run python -i examples/monitor.py

Then use:
    >>> status()        # System overview in a box
    >>> cpu()           # CPU usage bars
    >>> memory()        # Memory statistics
    >>> disk()          # Disk usage chart
    >>> network()       # Network stats table
    >>> top()           # Top processes
"""

import os
import platform
import psutil
from datetime import datetime
from replkit2 import create_repl_app, state, command


@state
class SystemMonitor:
    """System monitoring tool with ASCII visualizations."""

    cpu_history: list[float]
    start_time: datetime

    def __init__(self):
        self.cpu_history = []
        self.start_time = datetime.now()

    @command(display="box", title="System Status")
    def status(self):
        """Show system overview."""
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return (
            f"Hostname: {platform.node()}\n"
            f"Platform: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Uptime: {uptime.days}d {hours}h {minutes}m {seconds}s\n"
            f"CPU Cores: {psutil.cpu_count()}\n"
            f"Load Average: {', '.join(f'{x:.2f}' for x in os.getloadavg())}"
        )

    @command(display="bar_chart")
    def cpu(self):
        """Show CPU usage per core."""
        cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)

        return {f"Core {i}": percent for i, percent in enumerate(cpu_percents)}

    @command(display="table", headers=["metric", "used", "total", "percent"])
    def memory(self):
        """Show memory usage statistics."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        def fmt_bytes(bytes):
            for unit in ["B", "KB", "MB", "GB"]:
                if bytes < 1024.0:
                    return f"{bytes:.1f}{unit}"
                bytes /= 1024.0
            return f"{bytes:.1f}TB"

        return [
            {
                "metric": "RAM",
                "used": fmt_bytes(mem.used),
                "total": fmt_bytes(mem.total),
                "percent": f"{mem.percent:.1f}%",
            },
            {
                "metric": "Swap",
                "used": fmt_bytes(swap.used),
                "total": fmt_bytes(swap.total),
                "percent": f"{swap.percent:.1f}%",
            },
        ]

    @command(display="bar_chart", show_values=True)
    def disk(self):
        """Show disk usage for all partitions."""
        partitions = psutil.disk_partitions()
        usage_data = {}

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                # Only show if > 1GB total
                if usage.total > 1024**3:
                    usage_data[partition.mountpoint] = usage.percent
            except PermissionError:
                pass

        return usage_data

    @command(
        display="table",
        headers=["interface", "sent", "recv", "packets_sent", "packets_recv"],
    )
    def network(self):
        """Show network interface statistics."""
        stats = psutil.net_io_counters(pernic=True)

        def fmt_bytes(bytes):
            for unit in ["B", "KB", "MB", "GB"]:
                if bytes < 1024.0:
                    return f"{bytes:.1f}{unit}"
                bytes /= 1024.0
            return f"{bytes:.1f}TB"

        return [
            {
                "interface": iface[:10],  # Truncate long names
                "sent": fmt_bytes(io.bytes_sent),
                "recv": fmt_bytes(io.bytes_recv),
                "packets_sent": str(io.packets_sent),
                "packets_recv": str(io.packets_recv),
            }
            for iface, io in stats.items()
            if io.bytes_sent > 0 or io.bytes_recv > 0  # Only active interfaces
        ][:5]  # Limit to 5 interfaces

    @command(display="table", headers=["pid", "name", "cpu%", "mem%", "status"])
    def top(self, count: int = 10):
        """Show top processes by CPU usage."""
        processes = []

        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                info = proc.info
                if info["cpu_percent"] is not None:
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"][:20],  # Truncate long names
                            "cpu%": f"{info['cpu_percent']:.1f}",
                            "mem%": f"{info['memory_percent']:.1f}",
                            "status": info["status"],
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage and return top N
        processes.sort(key=lambda x: float(x["cpu%"]), reverse=True)
        return processes[:count]

    @command(display="list", style="bullet")
    def alerts(self):
        """Check for system alerts."""
        alerts = []

        # CPU check
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 80:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")

        # Memory check
        mem = psutil.virtual_memory()
        if mem.percent > 85:
            alerts.append(f"High memory usage: {mem.percent:.1f}%")

        # Disk check
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                if usage.percent > 90:
                    alerts.append(f"Low disk space on {partition.mountpoint}: {usage.percent:.1f}% used")
            except Exception:
                pass

        return alerts if alerts else ["All systems normal"]

    @command
    def cpu_sparkline(self):
        """Show CPU usage trend (collects data over time)."""
        from replkit2.textkit import sparkline

        # Collect CPU samples
        self.cpu_history.append(psutil.cpu_percent(interval=0.1))
        # Keep last 50 samples
        self.cpu_history = self.cpu_history[-50:]

        if len(self.cpu_history) < 2:
            return "Collecting CPU data... (call this command multiple times)"

        return f"CPU Trend: {sparkline(self.cpu_history, width=40)}"

    @command(display="tree")
    def summary(self):
        """System summary in tree format."""
        cpu_count = psutil.cpu_count()
        mem = psutil.virtual_memory()

        return {
            "System": {
                "Hostname": platform.node(),
                "OS": f"{platform.system()} {platform.release()}",
            },
            "Resources": {
                "CPU": f"{cpu_count} cores @ {psutil.cpu_percent()}%",
                "Memory": f"{mem.percent:.1f}% used",
                "Processes": str(len(psutil.pids())),
            },
            "Storage": {
                partition.device: f"{usage.percent:.1f}% used"
                for partition in psutil.disk_partitions()
                if (usage := psutil.disk_usage(partition.mountpoint)).total > 1024**3
            },
        }


# Create app and inject commands
app = create_repl_app("monitor", SystemMonitor)

if __name__ == "__main__":
    print("System Monitor - TextKit Visualization Demo")
    print("=" * 50)
    print("Commands:")
    print("  status()         - System overview")
    print("  cpu()            - CPU usage per core")
    print("  memory()         - Memory statistics")
    print("  disk()           - Disk usage")
    print("  network()        - Network statistics")
    print("  top(count)       - Top processes")
    print("  alerts()         - System alerts")
    print("  cpu_sparkline()  - CPU trend (call multiple times)")
    print("  summary()        - Tree view summary")
    print()
    print("Try: status()")
    print()
