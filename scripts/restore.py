# scripts/restore.py
#!/usr/bin/env python3
import argparse
import glob
import logging
import os
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("restore.log"), logging.StreamHandler()],
)
logger = logging.getLogger("restore")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database and uploads restore script")
    parser.add_argument("--db-host", default="db", help="Database host")
    parser.add_argument("--db-port", default="5432", help="Database port")
    parser.add_argument("--db-name", default="star_competency", help="Database name")
    parser.add_argument("--db-user", default="user", help="Database user")
    parser.add_argument("--db-password", default="password", help="Database password")
    parser.add_argument("--backup-dir", default="./backups", help="Backup directory")
    parser.add_argument(
        "--uploads-dir",
        default="./data/uploads",
        help="Uploads directory to restore to",
    )
    parser.add_argument(
        "--db-backup",
        help="Specific database backup file to restore (defaults to latest)",
    )
    parser.add_argument(
        "--uploads-backup",
        help="Specific uploads backup file to restore (defaults to latest)",
    )
    return parser.parse_args()


def get_latest_backup(directory, prefix):
    """Get the latest backup file with the specified prefix."""
    if not os.path.exists(directory):
        logger.error(f"Backup directory does not exist: {directory}")
        return None

    pattern = os.path.join(
        directory, f"{prefix}_*.{'sql' if prefix == 'star_competency' else 'tar.gz'}"
    )
    files = glob.glob(pattern)

    if not files:
        logger.error(f"No backup files found matching pattern: {pattern}")
        return None

    # Sort by modification time (newest first)
    latest = max(files, key=os.path.getmtime)
    logger.info(f"Found latest backup: {latest}")
    return latest


def restore_database(backup_file, args):
    """Restore PostgreSQL database from backup."""
    if not backup_file or not os.path.exists(backup_file):
        logger.error(f"Database backup file does not exist: {backup_file}")
        return False

    # Set environment variables for pg_restore
    env = os.environ.copy()
    env["PGPASSWORD"] = args.db_password

    try:
        # First, check if database exists and drop it
        check_cmd = [
            "psql",
            f"--host={args.db_host}",
            f"--port={args.db_port}",
            f"--username={args.db_user}",
            "--dbname=postgres",
            "-c",
            f"SELECT 1 FROM pg_database WHERE datname='{args.db_name}'",
        ]

        check_result = subprocess.run(
            check_cmd, env=env, capture_output=True, text=True
        )
        if "1 row" in check_result.stdout:
            logger.info(f"Database {args.db_name} exists, dropping it")
            drop_cmd = [
                "psql",
                f"--host={args.db_host}",
                f"--port={args.db_port}",
                f"--username={args.db_user}",
                "--dbname=postgres",
                "-c",
                f"DROP DATABASE {args.db_name}",
            ]
            subprocess.run(drop_cmd, env=env, check=True)

        # Create new database
        create_cmd = [
            "psql",
            f"--host={args.db_host}",
            f"--port={args.db_port}",
            f"--username={args.db_user}",
            "--dbname=postgres",
            "-c",
            f"CREATE DATABASE {args.db_name}",
        ]
        subprocess.run(create_cmd, env=env, check=True)

        # Restore backup
        logger.info(f"Restoring database from {backup_file}")
        restore_cmd = [
            "pg_restore",
            f"--host={args.db_host}",
            f"--port={args.db_port}",
            f"--username={args.db_user}",
            f"--dbname={args.db_name}",
            "--no-owner",
            backup_file,
        ]

        result = subprocess.run(restore_cmd, env=env, check=True, capture_output=True)
        logger.info("Database restore completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Database restore failed: {e}")
        logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'None'}")
        return False


def restore_uploads(backup_file, args):
    """Restore uploads from backup."""
    if not backup_file or not os.path.exists(backup_file):
        logger.error(f"Uploads backup file does not exist: {backup_file}")
        return False

    # Create uploads directory if it doesn't exist
    os.makedirs(os.path.dirname(args.uploads_dir), exist_ok=True)

    # Remove existing uploads directory if it exists
    if os.path.exists(args.uploads_dir):
        logger.info(f"Removing existing uploads directory: {args.uploads_dir}")
        subprocess.run(["rm", "-rf", args.uploads_dir], check=True)

    try:
        logger.info(f"Restoring uploads from {backup_file}")
        result = subprocess.run(
            ["tar", "-xzf", backup_file, "-C", os.path.dirname(args.uploads_dir)],
            check=True,
            capture_output=True,
        )

        logger.info("Uploads restore completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Uploads restore failed: {e}")
        logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'None'}")
        return False


def main():
    args = parse_args()

    # Get backup files
    db_backup = args.db_backup or get_latest_backup(args.backup_dir, args.db_name)
    uploads_backup = args.uploads_backup or get_latest_backup(
        args.backup_dir, "uploads"
    )

    # Restore database
    if db_backup:
        db_success = restore_database(db_backup, args)
        logger.info(f"Database restore {'successful' if db_success else 'failed'}")
    else:
        logger.error("No database backup file specified or found")

    # Restore uploads
    if uploads_backup:
        uploads_success = restore_uploads(uploads_backup, args)
        logger.info(f"Uploads restore {'successful' if uploads_success else 'failed'}")
    else:
        logger.error("No uploads backup file specified or found")

    logger.info("Restore process completed")


if __name__ == "__main__":
    main()
