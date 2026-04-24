import argparse
import os
import subprocess
import sys
import time
from urllib.request import urlopen
from pathlib import Path


def run_checked(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def http_up(url, timeout=2):
    try:
        with urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def launch_background(cmd, cwd):
    kwargs = {"cwd": str(cwd)}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    return subprocess.Popen(cmd, **kwargs)


def wait_http(url, retries=10, delay=1.0):
    for _ in range(retries):
        if http_up(url):
            return True
        time.sleep(delay)
    return False


def print_status(backend_proc, frontend_proc, backend_only=False):
    backend_health = "http://127.0.0.1:5000/api/health"
    backend_ok = backend_proc.poll() is None and wait_http(backend_health, retries=12, delay=0.75)

    frontend_url = "http://localhost:3000"
    frontend_ok = True
    if not backend_only:
        frontend_ok = frontend_proc.poll() is None and wait_http(frontend_url, retries=8, delay=0.75)

    print("\n=== Startup Status ===")
    print(f"Backend process: {'RUNNING' if backend_proc.poll() is None else 'EXITED'}")
    print(f"Backend health: {'UP' if backend_ok else 'DOWN'}")
    print("Backend URL: http://127.0.0.1:5000")
    print("Backend Health URL: http://127.0.0.1:5000/api/health")

    if not backend_only:
        print(f"Frontend process: {'RUNNING' if frontend_proc.poll() is None else 'EXITED'}")
        print(f"Frontend URL status: {'UP' if frontend_ok else 'DOWN'}")
        print("Frontend URL: http://localhost:3000")

    if not backend_only and not frontend_ok:
        print("Hint: If frontend is DOWN on this machine, Windows policy may be blocking Rollup native binaries.")

    print("\nTip: Stop services by closing their terminal windows.")


def main():
    parser = argparse.ArgumentParser(description="Start backend and frontend for mba_project.")
    parser.add_argument("--install-deps", action="store_true", help="Install backend/frontend dependencies before start.")
    parser.add_argument("--generate-data", action="store_true", help="Generate synthetic CSV before start.")
    parser.add_argument("--backend-only", action="store_true", help="Start only backend.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    backend_dir = repo_root / "backend"
    frontend_dir = repo_root / "frontend"
    venv_python = backend_dir / "venv" / "Scripts" / "python.exe"

    if not venv_python.exists():
        print("Backend virtual environment not found. Creating venv...")
        run_checked([sys.executable, "-m", "venv", "venv"], cwd=str(backend_dir))

    if args.install_deps:
        run_checked([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=str(backend_dir))
        if not args.backend_only:
            run_checked(["npm", "install"], cwd=str(frontend_dir))

    if args.generate_data:
        run_checked([str(venv_python), "data_generator.py"], cwd=str(backend_dir))

    print("Starting backend...")
    backend_proc = launch_background([str(venv_python), "app.py"], backend_dir)

    frontend_proc = None
    if not args.backend_only:
        print("Starting frontend...")
        if os.name == "nt":
            frontend_proc = launch_background(["cmd", "/c", "npm", "run", "dev"], frontend_dir)
        else:
            frontend_proc = launch_background(["npm", "run", "dev"], frontend_dir)

    print_status(backend_proc, frontend_proc, backend_only=args.backend_only)


if __name__ == "__main__":
    main()
