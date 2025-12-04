"""
Database Backup Utility for PROTECH
Handles PostgreSQL database backup operations
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from django.conf import settings
import logging
import sys
import shutil

logger = logging.getLogger(__name__)


def find_pg_dump():
    """
    Find pg_dump executable on the system
    Returns the full path to pg_dump or 'pg_dump' if found in PATH
    """
    # First, check if pg_dump is in PATH
    pg_dump_path = shutil.which('pg_dump')
    if pg_dump_path:
        return pg_dump_path
    
    # On Windows, check common PostgreSQL installation paths
    if sys.platform == 'win32':
        possible_paths = [
            r'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\15\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\14\bin\pg_dump.exe',
            r'C:\Program Files (x86)\PostgreSQL\17\bin\pg_dump.exe',
            r'C:\Program Files (x86)\PostgreSQL\16\bin\pg_dump.exe',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    # Return default if not found (will fail later with clear error)
    return 'pg_dump'


def log_backup_to_database(backup_type, status, filename, filepath, file_size_bytes, error_message=None, user=None):
    """
    Log backup operation to database
    
    Args:
        backup_type: 'MANUAL' or 'AUTOMATIC'
        status: 'SUCCESS' or 'FAILED'
        filename: Name of backup file
        filepath: Full path to backup file
        file_size_bytes: File size in bytes
        error_message: Error message if failed
        user: User who initiated (for manual backups)
    """
    try:
        from PROTECHAPP.models import BackupLog
        
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        
        BackupLog.objects.create(
            backup_type=backup_type,
            status=status,
            filename=filename,
            filepath=filepath,
            file_size_bytes=file_size_bytes,
            file_size_mb=file_size_mb,
            error_message=error_message,
            initiated_by=user
        )
        logger.info(f"Backup logged to database: {filename}")
    except Exception as e:
        logger.error(f"Failed to log backup to database: {e}")


def get_backup_directory():
    """Get or create the backup directory"""
    backup_dir = Path(settings.BASE_DIR) / "database backup"
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def generate_backup_filename():
    """Generate a timestamped backup filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"protech_backup_{timestamp}.sql"


def create_database_backup(output_path=None, backup_type='MANUAL', user=None):
    """
    Create a PostgreSQL database backup using pg_dump
    
    Args:
        output_path: Optional custom path for the backup file
        backup_type: 'MANUAL' or 'AUTOMATIC'
        user: User who initiated the backup (for manual backups)
        
    Returns:
        tuple: (success: bool, filepath: str, error_message: str)
    """
    filename = None
    filepath = None
    file_size = 0
    
    try:
        # Get database configuration
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']
        
        # Determine output file path
        if output_path is None:
            backup_dir = get_backup_directory()
            filename = generate_backup_filename()
            output_path = backup_dir / filename
        else:
            filename = os.path.basename(output_path)
        
        filepath = str(output_path)
        
        # Find pg_dump executable
        pg_dump_exe = find_pg_dump()
        
        # Check if pg_dump is available
        try:
            subprocess.run([pg_dump_exe, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = (
                "pg_dump command not found. Please install PostgreSQL client tools:\n"
                "Windows: Download from https://www.postgresql.org/download/windows/\n"
                "Ubuntu/Linux: sudo apt-get install postgresql-client\n"
                "After installation, add PostgreSQL bin directory to system PATH."
            )
            logger.error(error_msg)
            
            # Log failure to database
            log_backup_to_database(
                backup_type=backup_type,
                status='FAILED',
                filename=filename or 'unknown',
                filepath=filepath or '',
                file_size_bytes=0,
                error_message=error_msg,
                user=user
            )
            
            return False, None, error_msg
        
        # Prepare pg_dump command with found executable
        # Using -Fp for plain text SQL format (more portable)
        pg_dump_cmd = [
            pg_dump_exe,
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-F', 'p',  # Plain text format
            '-f', filepath,
            db_name
        ]
        
        # Set environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Execute pg_dump
        logger.info(f"Starting database backup using {pg_dump_exe} to {filepath}")
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            # Get file size
            file_size = os.path.getsize(filepath)
            
            logger.info(f"Database backup completed successfully: {filepath}")
            
            # Log to database
            log_backup_to_database(
                backup_type=backup_type,
                status='SUCCESS',
                filename=filename,
                filepath=filepath,
                file_size_bytes=file_size,
                user=user
            )
            
            return True, filepath, None
        else:
            error_msg = f"pg_dump failed: {result.stderr}"
            logger.error(error_msg)
            
            # Log failure to database
            log_backup_to_database(
                backup_type=backup_type,
                status='FAILED',
                filename=filename or 'unknown',
                filepath=filepath or '',
                file_size_bytes=0,
                error_message=error_msg,
                user=user
            )
            
            return False, None, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "Database backup timed out after 5 minutes"
        logger.error(error_msg)
        
        log_backup_to_database(
            backup_type=backup_type,
            status='FAILED',
            filename=filename or 'unknown',
            filepath=filepath or '',
            file_size_bytes=0,
            error_message=error_msg,
            user=user
        )
        
        return False, None, error_msg
        
    except FileNotFoundError:
        error_msg = "pg_dump command not found. Please ensure PostgreSQL client tools are installed."
        logger.error(error_msg)
        
        log_backup_to_database(
            backup_type=backup_type,
            status='FAILED',
            filename=filename or 'unknown',
            filepath=filepath or '',
            file_size_bytes=0,
            error_message=error_msg,
            user=user
        )
        
        return False, None, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error during backup: {str(e)}"
        logger.error(error_msg)
        
        log_backup_to_database(
            backup_type=backup_type,
            status='FAILED',
            filename=filename or 'unknown',
            filepath=filepath or '',
            file_size_bytes=0,
            error_message=error_msg,
            user=user
        )
        
        return False, None, error_msg


def cleanup_old_backups(keep_count=30):
    """
    Clean up old backup files, keeping only the most recent ones
    
    Args:
        keep_count: Number of recent backups to keep (default: 30)
    """
    try:
        backup_dir = get_backup_directory()
        backup_files = sorted(
            backup_dir.glob("protech_backup_*.sql"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Delete old backups beyond keep_count
        for old_backup in backup_files[keep_count:]:
            try:
                old_backup.unlink()
                logger.info(f"Deleted old backup: {old_backup}")
            except Exception as e:
                logger.error(f"Failed to delete {old_backup}: {e}")
                
    except Exception as e:
        logger.error(f"Error during backup cleanup: {e}")


def get_backup_list():
    """
    Get list of all backup files with their metadata
    
    Returns:
        list: List of dictionaries containing backup file info
    """
    try:
        backup_dir = get_backup_directory()
        backup_files = []
        
        for backup_file in sorted(
            backup_dir.glob("protech_backup_*.sql"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        ):
            stat_info = backup_file.stat()
            backup_files.append({
                'filename': backup_file.name,
                'filepath': str(backup_file),
                'size_bytes': stat_info.st_size,
                'size_mb': round(stat_info.st_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(stat_info.st_mtime),
            })
        
        return backup_files
        
    except Exception as e:
        logger.error(f"Error getting backup list: {e}")
        return []
