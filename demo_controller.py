import os
import queue
import shutil
import socket
import subprocess
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import scrolledtext, ttk


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / "dbt-env" / "Scripts" / "python.exe"
DBT = ROOT / "dbt-env" / "Scripts" / "dbt.exe"
DBT_PROJECT = ROOT / "dbt_project" / "iot_analytics"
LOGS = ROOT / "logs" / "demo"
DASHBOARD_URL = "http://localhost:8503"
BUILD_INTERVAL = 20
FLAGS = subprocess.CREATE_NO_WINDOW

messages = queue.Queue()
stop_event = threading.Event()
worker = None
children = {}
log_handles = []
close_requested = False


class StopRequested(Exception):
    pass


def report(message):
    timestamp = time.strftime("%H:%M:%S")
    messages.put(f"[{timestamp}] {message}")


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def check_stop():
    if stop_event.is_set():
        raise StopRequested()


def pause(seconds):
    if stop_event.wait(seconds):
        raise StopRequested()


def command(args, timeout=60, cwd=ROOT):
    result = subprocess.run(
        [str(arg) for arg in args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        creationflags=FLAGS,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "No output").strip()
        raise RuntimeError(detail[-2500:])
    return result.stdout.strip()


def docker_ready():
    try:
        command(["docker", "info"], timeout=10)
        return True
    except Exception:
        return False


def wait_until(test, description, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        check_stop()
        if test():
            return
        pause(2)
    raise RuntimeError(f"Timed out waiting for {description}.")


def start_process(name, args):
    handle = open(LOGS / f"{name}.log", "a", encoding="utf-8")
    log_handles.append(handle)
    handle.write(f"\n--- Started {time.ctime()} ---\n")
    handle.flush()

    process = subprocess.Popen(
        [str(arg) for arg in args],
        cwd=str(ROOT),
        stdout=handle,
        stderr=subprocess.STDOUT,
        creationflags=FLAGS,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    children[name] = process
    report(f"Started {name}.")


def check_processes():
    for name, process in children.items():
        if process.poll() is not None:
            raise RuntimeError(
                f"{name} exited with code {process.returncode}. "
                f"Open logs/demo/{name}.log for details."
            )


def stop_process(name):
    process = children.pop(name, None)
    if process is None or process.poll() is not None:
        return

    subprocess.run(
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=FLAGS,
    )
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        report(f"Could not confirm that {name} stopped.")
    else:
        report(f"Stopped {name}.")


def build_models():
    report("Running dbt build...")
    started = time.strftime("%H:%M:%S")

    result = subprocess.run(
        [str(DBT), "build"],
        cwd=str(DBT_PROJECT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        timeout=180,
        creationflags=FLAGS,
    )

    with open(LOGS / "dbt.log", "a", encoding="utf-8") as handle:
        handle.write(f"\n--- Build started {started} ---\n")
        handle.write(result.stdout or "")

    if result.returncode != 0:
        raise RuntimeError("dbt build failed. Open logs/demo/dbt.log.")

    report("dbt build passed. Dashboard summaries updated.")


def run_demo():
    containers_managed = False
    try:
        LOGS.mkdir(parents=True, exist_ok=True)

        for path in [
            PYTHON,
            DBT,
            DBT_PROJECT / "dbt_project.yml",
            ROOT / "dashboard" / "app.py",
            ROOT / "simulator" / "publish_sensors.py",
            ROOT / "ingestion" / "subscribe_to_postgres.py",
        ]:
            if not path.exists():
                raise RuntimeError(f"Missing file: {path}")

        if shutil.which("docker") is None:
            raise RuntimeError("Docker was not found in PATH.")

        if port_open(8503):
            raise RuntimeError(
                "Port 8503 is already in use. Stop the old dashboard "
                "with Ctrl+C, then click Start Demo again."
            )

        check_stop()
        if not docker_ready():
            report("Starting Docker Desktop...")
            command(["docker", "desktop", "start"], timeout=180)
            wait_until(docker_ready, "Docker Desktop", 180)

        report("Docker is ready.")
        check_stop()

        report("Starting PostgreSQL and Mosquitto...")
        containers_managed = True
        command(
            ["docker", "compose", "up", "-d", "postgres", "mosquitto"],
            timeout=180,
        )

        wait_until(
            lambda: port_open(5432) and port_open(1883),
            "PostgreSQL and MQTT ports",
            90,
        )

        report("Database and MQTT ports are reachable.")
        check_stop()

        start_process(
            "subscriber",
            [PYTHON, "-u", ROOT / "ingestion" / "subscribe_to_postgres.py"],
        )
        pause(3)
        check_processes()

        start_process(
            "simulator",
            [PYTHON, "-u", ROOT / "simulator" / "publish_sensors.py"],
        )
        pause(5)
        check_processes()

        build_models()
        check_stop()
        check_processes()

        start_process(
            "dashboard",
            [
                PYTHON,
                "-m",
                "streamlit",
                "run",
                ROOT / "dashboard" / "app.py",
                "--server.port",
                "8503",
                "--server.headless",
                "true",
            ],
        )

        wait_until(lambda: port_open(8503), "dashboard", 60)
        check_processes()
        webbrowser.open(DASHBOARD_URL)
        report("DEMO RUNNING. Browser opened.")
        report("dbt refreshes after each 20-second interval.")

        while True:
            pause(BUILD_INTERVAL)
            check_processes()
            build_models()

    except StopRequested:
        report("Stop requested.")
    except Exception as exc:
        report(f"ERROR: {exc}")
    finally:
        report("Stopping demo processes...")
        stop_process("simulator")

        if "subscriber" in children:
            time.sleep(3)

        stop_process("subscriber")
        stop_process("dashboard")

        if containers_managed:
            report("Stopping project containers; stored data is retained.")
            try:
                command(
                    [
                        "docker",
                        "compose",
                        "stop",
                        "mosquitto",
                        "postgres",
                    ],
                    timeout=90,
                )
            except Exception as exc:
                report(f"Container stop error: {exc}")

        for handle in log_handles:
            handle.close()
        log_handles.clear()
        report("Controller idle.")


def start_demo():
    global worker

    if worker is not None and worker.is_alive():
        return

    stop_event.clear()
    worker = threading.Thread(target=run_demo, daemon=False)
    worker.start()


def stop_demo():
    if worker is not None and worker.is_alive():
        report(
            "Stop requested. Waiting for any active Docker command "
            "or dbt build to finish."
        )
        stop_event.set()


def close_window():
    global close_requested
    close_requested = True
    stop_demo()


def open_logs():
    LOGS.mkdir(parents=True, exist_ok=True)
    os.startfile(str(LOGS))


def update_ui():
    while True:
        try:
            message = messages.get_nowait()
        except queue.Empty:
            break

        output.configure(state="normal")
        output.insert(tk.END, message + "\n")
        output.see(tk.END)
        output.configure(state="disabled")

    running = worker is not None and worker.is_alive()
    start_button.configure(state="disabled" if running else "normal")
    stop_button.configure(state="normal" if running else "disabled")
    status.set(
        "Stopping..." if running and stop_event.is_set()
        else "Active — see progress below" if running
        else "Idle"
    )

    if close_requested and not running:
        window.destroy()
        return

    window.after(200, update_ui)


window = tk.Tk()
window.title("MQTT IoT Pipeline — Demo Controller")
window.geometry("850x540")

ttk.Label(
    window,
    text="MQTT IoT Analytics Pipeline",
    font=("Segoe UI", 18, "bold"),
).pack(pady=(18, 6))

ttk.Label(
    window,
    text="Docker → Ingestion → Simulator → dbt → Dashboard",
).pack()

buttons = ttk.Frame(window)
buttons.pack(pady=16)

start_button = ttk.Button(buttons, text="Start Demo", command=start_demo)
start_button.pack(side="left", padx=6)

stop_button = ttk.Button(buttons, text="Stop Demo", command=stop_demo)
stop_button.pack(side="left", padx=6)

ttk.Button(buttons, text="Open Logs", command=open_logs).pack(
    side="left", padx=6
)

status = tk.StringVar(value="Idle")
ttk.Label(window, textvariable=status).pack(pady=(0, 8))

output = scrolledtext.ScrolledText(
    window,
    height=20,
    font=("Consolas", 10),
    state="disabled",
)
output.pack(fill="both", expand=True, padx=16, pady=(0, 16))

window.protocol("WM_DELETE_WINDOW", close_window)
window.after(200, update_ui)
window.mainloop()