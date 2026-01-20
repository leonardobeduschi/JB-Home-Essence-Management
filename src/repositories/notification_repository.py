"""
Notification repository - PostgreSQL Compatible
"""

from typing import List, Dict
from src.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    """Repository for notification dismissals."""

    def __init__(self):
        super().__init__(filepath='', schema={}, table_name='notification_dismissals')

    def exists(self, item_id: str) -> bool:
        return False

    def is_dismissed(self, notification_type: str, notification_key: str) -> bool:
        """Check if a notification has been dismissed."""
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                if self.db_type == 'postgresql':
                    cur.execute(
                        'SELECT 1 FROM notification_dismissals WHERE notification_type = %s AND notification_key = %s LIMIT 1',
                        (notification_type, notification_key)
                    )
                else:
                    cur.execute(
                        'SELECT 1 FROM notification_dismissals WHERE notification_type = ? AND notification_key = ? LIMIT 1',
                        (notification_type, notification_key)
                    )
                return cur.fetchone() is not None
        except Exception as e:
            print(f"Error checking dismissal: {e}")
            return False

    def dismiss(self, notification_type: str, notification_key: str) -> bool:
        """Mark a notification as dismissed."""
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                if self.db_type == 'postgresql':
                    cur.execute(
                        'INSERT INTO notification_dismissals (notification_type, notification_key) VALUES (%s, %s) ON CONFLICT (notification_type, notification_key) DO NOTHING',
                        (notification_type, notification_key)
                    )
                else:
                    cur.execute(
                        'INSERT OR IGNORE INTO notification_dismissals (notification_type, notification_key) VALUES (?, ?)',
                        (notification_type, notification_key)
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error dismissing notification: {e}")
            return False

    def undismiss(self, notification_type: str, notification_key: str) -> bool:
        """Remove dismissal (restore notification)."""
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                if self.db_type == 'postgresql':
                    cur.execute(
                        'DELETE FROM notification_dismissals WHERE notification_type = %s AND notification_key = %s',
                        (notification_type, notification_key)
                    )
                else:
                    cur.execute(
                        'DELETE FROM notification_dismissals WHERE notification_type = ? AND notification_key = ?',
                        (notification_type, notification_key)
                    )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error undismissing notification: {e}")
            return False

    def get_all_dismissed(self) -> List[Dict]:
        """Get all dismissed notifications."""
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                cur.execute('SELECT * FROM notification_dismissals ORDER BY dismissed_at DESC')
                return [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"Error getting dismissed notifications: {e}")
            return []