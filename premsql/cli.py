import os
import subprocess
import sys
import json
import atexit
from pathlib import Path

import click

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# PID file for tracking spawned processes
PID_FILE = Path(user_cache_dir()) / "premsql" / "pids.json" if 'user_cache_dir' in dir() else Path.home() / ".premsql_pids.json"

def _get_pid_file():
    """Get the PID file path."""
    try:
        from platformdirs import user_cache_dir
        cache_dir = Path(user_cache_dir()) / "premsql"
    except ImportError:
        cache_dir = Path.home() / ".premsql_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "pids.json"


def _save_pid(service_name: str, pid: int):
    """Save a PID to the PID file."""
    pid_file = _get_pid_file()
    pids = {}
    if pid_file.exists():
        try:
            pids = json.load(pid_file.open("r"))
        except (json.JSONDecodeError, IOError):
            pids = {}
    pids[service_name] = pid
    json.dump(pids, pid_file.open("w"), indent=2)


def _load_pids():
    """Load all saved PIDs."""
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return {}
    try:
        return json.load(pid_file.open("r"))
    except (json.JSONDecodeError, IOError):
        return {}


def _clear_pid_file():
    """Clear the PID file."""
    pid_file = _get_pid_file()
    if pid_file.exists():
        pid_file.unlink()


def _stop_process_by_pid(pid: int, timeout: int = 5) -> bool:
    """Stop a process by its PID with timeout."""
    try:
        proc = subprocess.Popen(["ps", "-p", str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait(timeout=1)
        if proc.returncode == 0:
            # Process exists, send SIGTERM
            os.kill(pid, 15)  # SIGTERM
            # Wait for graceful shutdown
            import time
            for _ in range(timeout):
                try:
                    os.kill(pid, 0)  # Check if process still exists
                    time.sleep(1)
                except OSError:
                    return True  # Process terminated
            # Force kill if still running
            try:
                os.kill(pid, 9)  # SIGKILL
            except OSError:
                pass
            return True
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        pass
    return False


@click.group()
@click.version_option()
def cli():
    """PremSQL CLI to manage API servers and Streamlit app"""
    pass


@cli.group()
def launch():
    """Launch PremSQL services"""
    pass


@launch.command(name='all')
def launch_all():
    """Launch both API server and Streamlit app"""
    premsql_path = Path(__file__).parent.parent.absolute()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(premsql_path)

    # Start API server
    manage_py_path = premsql_path / "premsql" / "playground" / "backend" / "manage.py"
    if not manage_py_path.exists():
        click.echo(f"Error: manage.py not found at {manage_py_path}", err=True)
        sys.exit(1)

    # Run migrations first
    click.echo("Running database migrations...")
    try:
        subprocess.run([sys.executable, str(manage_py_path), "makemigrations"], env=env, check=True)
        subprocess.run([sys.executable, str(manage_py_path), "migrate"], env=env, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running migrations: {e}", err=True)
        sys.exit(1)

    click.echo("Starting the PremSQL backend API server...")
    api_process = subprocess.Popen(
        [sys.executable, str(manage_py_path), "runserver"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _save_pid("api_server", api_process.pid)

    # Launch the streamlit app
    click.echo("Starting the PremSQL Streamlit app...")
    main_py_path = premsql_path / "premsql" / "playground" / "frontend" / "main.py"
    if not main_py_path.exists():
        click.echo(f"Error: main.py not found at {main_py_path}", err=True)
        sys.exit(1)

    cmd = [sys.executable, "-m", "streamlit", "run", str(main_py_path), "--server.maxUploadSize=100"]
    try:
        streamlit_process = subprocess.Popen(cmd, env=env)
        _save_pid("streamlit", streamlit_process.pid)
        streamlit_process.wait()
    except KeyboardInterrupt:
        click.echo("Stopping all services...")
        stop()


@launch.command(name='api')
def launch_api():
    """Launch only the API server"""
    premsql_path = Path(__file__).parent.parent.absolute()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(premsql_path)
    manage_py_path = premsql_path / "premsql" / "playground" / "backend" / "manage.py"

    if not manage_py_path.exists():
        click.echo(f"Error: manage.py not found at {manage_py_path}", err=True)
        sys.exit(1)

    # Run makemigrations
    click.echo("Running database migrations...")
    try:
        subprocess.run([sys.executable, str(manage_py_path), "makemigrations"], env=env, check=True)
        subprocess.run([sys.executable, str(manage_py_path), "migrate"], env=env, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running migrations: {e}", err=True)
        sys.exit(1)

    click.echo("Starting the PremSQL backend API server...")
    cmd = [sys.executable, str(manage_py_path), "runserver"]
    try:
        api_process = subprocess.Popen(cmd, env=env)
        _save_pid("api_server", api_process.pid)
        api_process.wait()
    except KeyboardInterrupt:
        click.echo("API server stopped.")


@cli.command()
def stop():
    """Stop all PremSQL services using saved PIDs"""
    click.echo("Stopping all PremSQL services...")

    pids = _load_pids()
    if not pids:
        click.echo("No saved PIDs found. Services may not have been started via CLI.")
        return

    stopped_count = 0
    for service_name, pid in pids.items():
        click.echo(f"Stopping {service_name} (PID: {pid})...")
        if _stop_process_by_pid(pid):
            click.echo(f"  {service_name} stopped successfully.")
            stopped_count += 1
        else:
            click.echo(f"  {service_name} was not running or could not be stopped.")

    _clear_pid_file()
    click.echo(f"Stopped {stopped_count} service(s).")


@cli.command()
def status():
    """Show status of PremSQL services"""
    pids = _load_pids()
    if not pids:
        click.echo("No saved PIDs found.")
        return

    for service_name, pid in pids.items():
        try:
            os.kill(pid, 0)  # Check if process exists
            click.echo(f"{service_name}: running (PID: {pid})")
        except OSError:
            click.echo(f"{service_name}: not running (saved PID: {pid})")


if __name__ == "__main__":
    cli()
