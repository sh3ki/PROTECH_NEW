"""
Celery tasks for PROTECH
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from PROTECHAPP.backup_utils import create_database_backup, cleanup_old_backups

logger = get_task_logger(__name__)


@shared_task
def perform_daily_backup():
    """
    Perform automatic daily database backup at 00:00 Manila Time (16:00 UTC)
    """
    logger.info("Starting scheduled daily database backup")
    
    try:
        success, filepath, error_msg = create_database_backup(backup_type='AUTOMATIC', user=None)
        
        if success:
            logger.info(f"Daily backup completed successfully: {filepath}")
            
            # Clean up old backups, keep last 30
            cleanup_old_backups(keep_count=30)
            logger.info("Old backup cleanup completed")
            
            return {
                'status': 'success',
                'filepath': filepath,
                'message': 'Daily backup completed successfully'
            }
        else:
            logger.error(f"Daily backup failed: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'message': 'Daily backup failed'
            }
            
    except Exception as e:
        logger.error(f"Unexpected error during daily backup: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Daily backup encountered an error'
        }


@shared_task
def manual_backup(user_id=None):
    """
    Perform manual database backup (triggered by user)
    """
    logger.info("Starting manual database backup")
    
    try:
        # Get user if provided
        user = None
        if user_id:
            from PROTECHAPP.models import CustomUser
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                pass
        
        success, filepath, error_msg = create_database_backup(backup_type='MANUAL', user=user)
        
        if success:
            logger.info(f"Manual backup completed successfully: {filepath}")
            return {
                'status': 'success',
                'filepath': filepath,
                'message': 'Manual backup completed successfully'
            }
        else:
            logger.error(f"Manual backup failed: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'message': 'Manual backup failed'
            }
            
    except Exception as e:
        logger.error(f"Unexpected error during manual backup: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Manual backup encountered an error'
        }
