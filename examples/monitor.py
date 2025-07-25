#!/usr/bin/env python3
"""
Flask-style System Monitor Example

This example demonstrates:
- Flask-style command decorators
- Various display types (box, table, bar_chart, progress)
- Real-time system monitoring with psutil
- Clean state management

Run:
    uv run python examples/monitor.py

Then use:
    >>> status()        # System overview
    >>> cpu()           # CPU usage bars
    >>> memory()        # Memory statistics
    >>> disk()          # Disk usage
    >>> network()       # Network stats
    >>> processes()     # Top processes
"""

import os
import platform
import psutil
from datetime import datetime
from dataclasses import dataclass, field
from replkit2 import App
from replkit2.types.core import CommandMeta
from replkit2.textkit import compose, box


@dataclass
class MonitorState:
    """State container for system monitoring."""

    start_time: datetime = field(default_factory=datetime.now)
    cpu_history: list[float] = field(default_factory=list)
    max_history: int = 60


# Create the app
app = App("monitor", MonitorState)


# Register report display handler
@app.formatter.register("report")
def handle_report(data, meta, formatter):
    """Handle multi-section report display."""
    sections = []
    for title, section_data, opts in data:
        section_meta = CommandMeta(display=opts.get("display"), display_opts=opts)
        formatted = formatter.format(section_data, section_meta)
        if opts.get("box", True):
            sections.append(box(formatted, title=title))
        else:
            sections.append(formatted)
    return compose(*sections, spacing=1)


@app.command(display="table", headers=["Metric", "Value"])
def status(state):
    """Show system overview."""
    # Update CPU history
    cpu_percent = psutil.cpu_percent(interval=0.1)
    state.cpu_history.append(cpu_percent)
    if len(state.cpu_history) > state.max_history:
        state.cpu_history.pop(0)

    # Get system info
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    return [
        {"Metric": "Hostname", "Value": platform.node()},
        {"Metric": "Platform", "Value": f"{platform.system()} {platform.release()}"},
        {"Metric": "Python", "Value": platform.python_version()},
        {"Metric": "Uptime", "Value": f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"},
        {"Metric": "", "Value": ""},  # Separator row
        {"Metric": "CPU Usage", "Value": f"{cpu_percent:.1f}%"},
        {"Metric": "CPU Cores", "Value": f"{psutil.cpu_count()} ({psutil.cpu_count(logical=False)} physical)"},
        {
            "Metric": "Load Average",
            "Value": " ".join(f"{x:.2f}" for x in os.getloadavg()) if hasattr(os, "getloadavg") else "N/A",
        },
        {"Metric": "", "Value": ""},  # Separator row
        {"Metric": "Memory Used", "Value": f"{psutil.virtual_memory().percent:.1f}%"},
        {"Metric": "Swap Used", "Value": f"{psutil.swap_memory().percent:.1f}%"},
        {"Metric": "Processes", "Value": str(len(psutil.pids()))},
    ]


@app.command(display="bar_chart", show_values=True)
def cpu(state, per_core: bool = False):
    """Show CPU usage.

    Args:
        per_core: Show per-core usage instead of overall
    """
    if per_core:
        # Per-core CPU usage
        percentages = psutil.cpu_percent(interval=0.1, percpu=True)
        return {f"Core {i}": pct for i, pct in enumerate(percentages)}
    else:
        # Overall CPU with categories
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        return {
            "User": cpu_times.user,
            "System": cpu_times.system,
            "Idle": cpu_times.idle,
            "Nice": getattr(cpu_times, "nice", 0),
            "IOWait": getattr(cpu_times, "iowait", 0),
        }


@app.command(display="table", headers=["Type", "Metric", "Value"])
def memory(state):
    """Show memory statistics."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    def format_bytes(bytes):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"

    return [
        {"Type": "Memory", "Metric": "Total", "Value": format_bytes(mem.total)},
        {"Type": "Memory", "Metric": "Used", "Value": f"{format_bytes(mem.used)} ({mem.percent:.1f}%)"},
        {"Type": "Memory", "Metric": "Free", "Value": format_bytes(mem.free)},
        {"Type": "Memory", "Metric": "Available", "Value": format_bytes(mem.available)},
        {"Type": "", "Metric": "", "Value": ""},  # Separator
        {"Type": "Swap", "Metric": "Total", "Value": format_bytes(swap.total)},
        {"Type": "Swap", "Metric": "Used", "Value": f"{format_bytes(swap.used)} ({swap.percent:.1f}%)"},
        {"Type": "Swap", "Metric": "Free", "Value": format_bytes(swap.free)},
    ]


@app.command(display="progress", show_percentage=True)
def disk(state, path: str = "/"):
    """Show disk usage for a path.

    Args:
        path: Path to check (default: root)
    """
    try:
        usage = psutil.disk_usage(path)
        return {"value": usage.used, "total": usage.total, "label": f"Disk usage for {path}"}
    except Exception as e:
        return {"value": 0, "total": 100, "label": f"Error: {e}"}


@app.command(display="table", headers=["Interface", "Status", "Sent", "Received", "Packets"])
def network(state):
    """Show network interface statistics."""
    stats = psutil.net_io_counters(pernic=True)
    addrs = psutil.net_if_addrs()

    def format_bytes(bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024.0
        return f"{bytes:.1f}TB"

    result = []
    for iface, io in stats.items():
        # Get status
        status = "UP" if iface in addrs and any(addr.address for addr in addrs[iface]) else "DOWN"

        result.append(
            {
                "Interface": iface[:15],  # Truncate long names
                "Status": status,
                "Sent": format_bytes(io.bytes_sent),
                "Received": format_bytes(io.bytes_recv),
                "Packets": f"{io.packets_sent}/{io.packets_recv}",
            }
        )

    return result


@app.command(display="table", headers=["PID", "Name", "CPU%", "Memory%", "Status"])
def processes(state, limit: int = 10):
    """Show top processes by CPU usage.

    Args:
        limit: Number of processes to show
    """
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            # Skip if we can't get CPU percent
            if info["cpu_percent"] is None:
                continue
            procs.append(
                {
                    "PID": info["pid"],
                    "Name": info["name"][:20],  # Truncate long names
                    "CPU%": f"{info['cpu_percent']:.1f}",
                    "Memory%": f"{info['memory_percent']:.1f}",
                    "Status": info["status"],
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort by CPU usage and return top N
    procs.sort(key=lambda x: float(x["CPU%"]), reverse=True)
    return procs[:limit]


@app.command(display="list")
def mounts(state):
    """List disk partitions and mount points."""
    partitions = psutil.disk_partitions()

    result = []
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            result.append(f"{part.device} -> {part.mountpoint} ({part.fstype}, {usage.percent:.1f}% used)")
        except PermissionError:
            result.append(f"{part.device} -> {part.mountpoint} ({part.fstype}, permission denied)")

    return result


@app.command(display="tree")
def temps(state):
    """Show temperature sensors (if available)."""
    if not hasattr(psutil, "sensors_temperatures"):
        return {"Error": ["Temperature sensors not available on this platform"]}

    temps = psutil.sensors_temperatures()
    if not temps:
        return {"Error": ["No temperature sensors found"]}

    result = {}
    for name, entries in temps.items():
        sensor_data = []
        for entry in entries:
            label = entry.label or "Sensor"
            temp = f"{entry.current:.1f}C"
            if entry.high:
                temp += f" (high: {entry.high:.1f}C)"
            sensor_data.append(f"{label}: {temp}")
        result[name] = sensor_data

    return result


@app.command(display="report")
def report(state):
    """Generate a full system report."""
    return [
        ("System Status", status(state), {"display": "table", "headers": ["Metric", "Value"]}),
        ("CPU Usage", cpu(state), {"display": "bar_chart"}),
        ("Top Processes", processes(state, limit=5), {"display": "table"}),
        ("Network", network(state), {"display": "table"}),
    ]


if __name__ == "__main__":
    app.run(title="Flask-style System Monitor")
