import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus


def find_mysql_client(custom_path: str | None = None) -> str:
    if custom_path:
        candidate = Path(custom_path)
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"mysql client not found at: {custom_path}")

    in_path = shutil.which("mysql")
    if in_path:
        return in_path

    common_windows_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
        r"C:\xampp\mysql\bin\mysql.exe",
    ]
    for path in common_windows_paths:
        if Path(path).exists():
            return path

    raise FileNotFoundError(
        "mysql client not found. Install MySQL client or pass --mysql-client-path."
    )


def run_command(command: list[str], env: dict[str, str], stdin_file=None) -> None:
    subprocess.run(command, check=True, env=env, stdin=stdin_file)


def build_mysql_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    safe_host = host.strip()
    return f"mysql+pymysql://{safe_user}:{safe_password}@{safe_host}:{port}/{db_name}"


def write_env_files(repo_root: Path, mysql_uri: str, jwt_secret: str) -> None:
    ps1_content = (
        f'$env:MYSQL_URI="{mysql_uri}"\n'
        f'$env:JWT_SECRET_KEY="{jwt_secret}"\n'
        "Write-Host \"Environment variables loaded for this terminal.\"\n"
    )
    (repo_root / "backend_env.ps1").write_text(ps1_content, encoding="utf-8")

    cmd_content = (
        f"set MYSQL_URI={mysql_uri}\n"
        f"set JWT_SECRET_KEY={jwt_secret}\n"
        "echo Environment variables loaded for this terminal.\n"
    )
    (repo_root / "backend_env.cmd").write_text(cmd_content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up MySQL database and import SQL dump for mba_project."
    )
    parser.add_argument("--mysql-host", default="localhost", help="MySQL host")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--mysql-user", default="root", help="MySQL username")
    parser.add_argument("--mysql-password", default="", help="MySQL password (optional prompt if empty)")
    parser.add_argument("--db-name", default="mba_ecommerce", help="Database name to create/import")
    parser.add_argument(
        "--dump-file",
        default="data/mba_ecommerce_full_dump.sql",
        help="Path to SQL dump file relative to repo root",
    )
    parser.add_argument(
        "--mysql-client-path",
        default="",
        help="Optional full path to mysql client executable",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Only create database, do not import dump file",
    )
    parser.add_argument(
        "--write-env-files",
        action="store_true",
        help="Write backend_env.ps1 and backend_env.cmd with current credentials",
    )
    parser.add_argument(
        "--jwt-secret",
        default="change-me-before-production",
        help="JWT secret to place in generated env helper files",
    )

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent

    password = args.mysql_password
    if password == "":
        password = getpass.getpass("MySQL password: ")

    try:
        mysql_client = find_mysql_client(args.mysql_client_path or None)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    dump_path = (repo_root / args.dump_file).resolve()
    if not args.skip_import and not dump_path.exists():
        print(f"Dump file not found: {dump_path}")
        print("Use --skip-import to only create database or pass --dump-file.")
        return 1

    env = os.environ.copy()
    env["MYSQL_PWD"] = password

    base_command = [
        mysql_client,
        "-h",
        args.mysql_host,
        "-P",
        str(args.mysql_port),
        "-u",
        args.mysql_user,
    ]

    create_db_sql = (
        f"CREATE DATABASE IF NOT EXISTS `{args.db_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )

    try:
        print("Creating database if it does not exist...")
        run_command(base_command + ["-e", create_db_sql], env)

        if not args.skip_import:
            print(f"Importing dump from: {dump_path}")
            with dump_path.open("rb") as sql_input:
                run_command(base_command + [args.db_name], env, stdin_file=sql_input)

        mysql_uri = build_mysql_uri(
            args.mysql_user,
            password,
            args.mysql_host,
            args.mysql_port,
            args.db_name,
        )
        print("\nSetup complete.")
        print(f"MYSQL_URI: {mysql_uri}")

        if args.write_env_files:
            write_env_files(repo_root, mysql_uri, args.jwt_secret)
            print("Generated env helper files:")
            print("- backend_env.ps1")
            print("- backend_env.cmd")

    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}")
        return exc.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
