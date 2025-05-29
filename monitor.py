import subprocess
import time
import re
import sys
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text

console = Console()

def get_tcp_congestion_algo():
    try:
        output = subprocess.check_output(["sysctl", "net.ipv4.tcp_congestion_control"], text=True)
        match = re.search(r"net\.ipv4\.tcp_congestion_control\s+=\s+(\w+)", output)
        return match.group(1) if match else "unknown"
    except Exception:
        return "unknown"

def parse_ss_output():
    try:
        result = subprocess.run(["ss", "-tni"], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    lines = result.stdout.strip().split("\n")
    pairs = []
    i = 0
    while i < len(lines):
        if "ESTAB" in lines[i] and ":22" not in lines[i]:
            meta = lines[i]
            if i + 1 < len(lines):
                stats = lines[i + 1]
                pairs.append((meta, stats))
            i += 2
        else:
            i += 1
    return pairs

def grep(pattern, text):
    match = re.search(pattern, text)
    return match.group(1) if match else "N/A"

def extract_values(meta, stats):
    local_ip = meta.split()[3]
    remote_ip = meta.split()[4]

    return {
        "local": local_ip,
        "remote": remote_ip,
        "rtt": grep(r"rtt:(\d+\.\d+)", stats),
        "cwnd": grep(r"cwnd:(\d+)", stats),
        "rate": int(grep(r"delivery_rate (\d+)", stats)) if grep(r"delivery_rate (\d+)", stats).isdigit() else 0,
        "pacing": int(grep(r"pacing_rate (\d+)", stats)) if grep(r"pacing_rate (\d+)", stats).isdigit() else 0,
        "lastsnd": float(grep(r"lastsnd:(\d+)", stats)) / 1000 if grep(r"lastsnd:(\d+)", stats).isdigit() else -1,
        "lastrcv": float(grep(r"lastrcv:(\d+)", stats)) / 1000 if grep(r"lastrcv:(\d+)", stats).isdigit() else -1,
        "lastack": float(grep(r"lastack:(\d+)", stats)) / 1000 if grep(r"lastack:(\d+)", stats).isdigit() else -1
    }

def format_bytes_per_sec(bps):
    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.2f} GB/s"
    elif bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} MB/s"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} KB/s"
    else:
        return f"{bps} B/s"

def colorize_rate(rate):
    if rate < 300_000:
        return "red"
    elif rate < 1_000_000:
        return "yellow"
    return "green"

def colorize_pacing(pacing):
    if pacing < 1_000_000:
        return "red"
    elif pacing < 5_000_000:
        return "yellow"
    return "green"

def colorize_rtt(rtt_val):
    try:
        rtt = float(rtt_val)
        if rtt < 30:
            return "green"
        elif rtt < 100:
            return "yellow"
        else:
            return "red"
    except:
        return "white"

def generate_table():
    table = Table(title="PoP-node TCP Monitor", show_lines=True)
    table.add_column("Local ⇄ Remote", style="bold cyan")
    table.add_column("RTT (ms)")
    table.add_column("CWND")
    table.add_column("Rate")
    table.add_column("Pacing")
    table.add_column("Last Send (s)")
    table.add_column("Last Recv (s)")
    table.add_column("Last ACK (s)")

    connections = parse_ss_output()
    for meta, stats in connections:
        conn = extract_values(meta, stats)
        clean_local = conn['local'].replace('[::ffff:', '').replace(']', '')
        clean_remote = conn['remote'].replace('[::ffff:', '').replace(']', '')

        rtt_text = Text(conn["rtt"], style=colorize_rtt(conn["rtt"]))
        rate_text = Text(format_bytes_per_sec(conn["rate"]), style=colorize_rate(conn["rate"]))
        pacing_text = Text(format_bytes_per_sec(conn["pacing"]), style=colorize_pacing(conn["pacing"]))

        table.add_row(
            f"{clean_local} ⇄ {clean_remote}",
            rtt_text,
            conn["cwnd"],
            rate_text,
            pacing_text,
            f"{conn['lastsnd']:.2f}" if conn["lastsnd"] >= 0 else "N/A",
            f"{conn['lastrcv']:.2f}" if conn["lastrcv"] >= 0 else "N/A",
            f"{conn['lastack']:.2f}" if conn["lastack"] >= 0 else "N/A",
        )

    tcp_algo = get_tcp_congestion_algo()
    table.caption = f"Total Active Connections: {len(connections)} • TCP Algorithm: {tcp_algo}"
    return table

def main():
    with Live(generate_table(), refresh_per_second=4, screen=True) as live:
        try:
            while True:
                time.sleep(0.25)
                live.update(generate_table())
        except KeyboardInterrupt:
            console.print("\n[yellow]Terminated by user.[/yellow]\n")
            sys.exit(0)

if __name__ == "__main__":
    main()
