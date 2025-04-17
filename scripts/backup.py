# scripts/backup.py

#!/usr/bin/env python3
import argparse
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("backup.log"), logging.StreamHandler()],
)
logger = logging.getLogger("backup")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Database backup script")
    parser.add_argument("--db-host", default="db", help="Database host")
    parser.add_argument("--db-port", default="5432", help="Database port")
    parser.add_argument("--db-name", default="star_competency", help="Database name")
    parser.add_argument("--db-user", default="user", help="Database user")
    parser.add_argument("--db-password", default="password", help="Database password")
    parser.add_argument(
        "--output-dir", default="./backups", help="Backup output directory"
    )
    parser.add_argument(
        "--keep-days", type=int, default=30, help="Number of days to keep backups"
    )
    parser.add_argument(
        "--uploads-dir", default="./data/uploads", help="Uploads directory to backup"
    )
    return parser.parse_args()


def create_backup_directory(directory):
    """Create backup directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created backup directory: {directory}")


def backup_database(args):
    """Backup PostgreSQL database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{args.db_name}_{timestamp}.sql"
    backup_path = os.path.join(args.output_dir, backup_filename)

    # Set environment variables for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = args.db_password

    # Run pg_dump command
    try:
        cmd = [
            "pg_dump",
            f"--host={args.db_host}",
            f"--port={args.db_port}",
            f"--username={args.db_user}",
            "--format=custom",
            f"--file={backup_path}",
            args.db_name,
        ]

        logger.info(f"Starting database backup to {backup_path}")
        result = subprocess.run(cmd, env=env, check=True, capture_output=True)
        logger.info("Database backup completed successfully")

        return backup_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup failed: {e}")
        logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'None'}")
        return None


def backup_uploads(args):
    """Backup uploads directory."""
    if not os.path.exists(args.uploads_dir):
        logger.warning(f"Uploads directory does not exist: {args.uploads_dir}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"uploads_{timestamp}.tar.gz"
    backup_path = os.path.join(args.output_dir, backup_filename)

    try:
        logger.info(f"Starting uploads backup to {backup_path}")
        result = subprocess.run(
            [
                "tar",
                "-czf",
                backup_path,
                "-C",
                os.path.dirname(args.uploads_dir),
                os.path.basename(args.uploads_dir),
            ],
            check=True,
            capture_output=True,
        )
        logger.info("Uploads backup completed successfully")

        return backup_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Uploads backup failed: {e}")
        logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'None'}")
        return None


def verify_database_backup(backup_path):
    """Verify the database backup."""
    if not backup_path or not os.path.exists(backup_path):
        logger.error(f"Cannot verify backup, file does not exist: {backup_path}")
        return False

    try:
        logger.info(f"Verifying database backup: {backup_path}")
        result = subprocess.run(
            ["pg_restore", "--list", backup_path], check=True, capture_output=True
        )

        if result.returncode == 0:
            logger.info("Database backup verification successful")
            return True
        else:
            logger.error(
                f"Database backup verification failed with code: {result.returncode}"
            )
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Database backup verification failed: {e}")
        logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'None'}")
        return False


def cleanup_old_backups(directory, keep_days):
    """Remove backups older than keep_days."""
    if not os.path.exists(directory):
        logger.warning(f"Backup directory does not exist: {directory}")
        return

    current_time = time.time()
    max_age = keep_days * 86400  # days to seconds

    logger.info(f"Cleaning up backups older than {keep_days} days")
    count = 0

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Skip if not a file
        if not os.path.isfile(file_path):
            continue

        # Check if file is a backup file
        if not (filename.endswith(".sql") or filename.endswith(".tar.gz")):
            continue

        # Check file age
        file_age = current_time - os.path.getmtime(file_path)
        if file_age > max_age:
            try:
                os.remove(file_path)
                count += 1
                logger.info(f"Removed old backup: {filename}")
            except Exception as e:
                logger.error(f"Failed to remove old backup {filename}: {e}")

    logger.info(f"Cleanup completed, removed {count} old backup files")


def main():
    args = parse_args()

    # Create backup directory
    create_backup_directory(args.output_dir)

    # Backup database
    db_backup_path = backup_database(args)

    # Verify database backup
    if db_backup_path:
        verify_database_backup(db_backup_path)

    # Backup uploads
    uploads_backup_path = backup_uploads(args)

    # Cleanup old backups
    cleanup_old_backups(args.output_dir, args.keep_days)

    # Log summary
    logger.info("Backup process completed")
    logger.info(f"Database backup: {db_backup_path or 'Failed'}")
    logger.info(f"Uploads backup: {uploads_backup_path or 'Failed'}")


if __name__ == "__main__":
    main()
