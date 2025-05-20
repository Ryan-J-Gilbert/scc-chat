"""
Event logging system for agentic chatbot using SQLite3
"""

import sqlite3
import os
import json
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from contextlib import contextmanager


class EventLogger:
    """Logger class for chatbot events using SQLite3"""

    # Event types
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    RETRIEVAL = "retrieval"
    ERROR = "error"

    def __init__(self, db_path: str = "chatbot_logs.db"):
        """Initialize the logger with the database path"""
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    @contextmanager
    def _get_cursor(self):
        """Context manager for database operations"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_db(self):
        """Create database tables if they don't exist"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_uuid TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user TEXT,
                event_type TEXT NOT NULL,
                tokens INTEGER,
                content TEXT
            )
            """
            )

            # Create index for faster lookups
            cursor.execute(
                """
            CREATE INDEX IF NOT EXISTS idx_events_chat_uuid ON events(chat_uuid)
            """
            )

    def log_event(
        self,
        chat_uuid: str,
        event_type: str,
        content: Union[str, Dict, List, None] = None,
        user: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> int:
        """Log a new event to the database"""
        timestamp = datetime.now().isoformat()

        # Convert dict/list content to JSON string
        if isinstance(content, (dict, list)):
            content = json.dumps(content)

        with self._get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO events (
                    chat_uuid, timestamp, user, event_type, tokens, content
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_uuid, timestamp, user, event_type, tokens, content),
            )
            return cursor.lastrowid

    def log_user_message(
        self, chat_uuid: str, message: str, user: str, tokens: Optional[int] = None
    ) -> int:
        """Log a message from the user"""
        return self.log_event(
            chat_uuid=chat_uuid,
            event_type=self.USER_MESSAGE,
            content=message,
            user=user,
            tokens=tokens,
        )

    def log_agent_response(
        self, chat_uuid: str, response: str, tokens: Optional[int] = None
    ) -> int:
        """Log a response from the agent"""
        return self.log_event(
            chat_uuid=chat_uuid,
            event_type=self.AGENT_RESPONSE,
            content=response,
            tokens=tokens,
        )

    def log_tool_call(self, chat_uuid: str, tool_data: Dict[str, Any]) -> int:
        """Log a tool call made by the agent"""
        return self.log_event(
            chat_uuid=chat_uuid, event_type=self.TOOL_CALL, content=tool_data
        )

    def log_retrieval(
        self, chat_uuid: str, query: str, results: List[Dict[str, Any]]
    ) -> int:
        """Log a retrieval operation"""
        content = {"query": query, "results": results}
        return self.log_event(
            chat_uuid=chat_uuid, event_type=self.RETRIEVAL, content=content
        )

    def log_error(self, chat_uuid: str, error_message: str) -> int:
        """Log an error event"""
        return self.log_event(
            chat_uuid=chat_uuid, event_type=self.ERROR, content=error_message
        )

    def get_chat_history(self, chat_uuid: str) -> List[Dict[str, Any]]:
        """Retrieve the complete history for a chat session"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, timestamp, user, event_type, tokens, content
                FROM events
                WHERE chat_uuid = ?
                ORDER BY timestamp ASC
                """,
                (chat_uuid,),
            )

            rows = cursor.fetchall()
            history = []

            for row in rows:
                id, timestamp, user, event_type, tokens, content = row

                # Try to parse content as JSON if it looks like JSON
                parsed_content = content
                if content and (content.startswith("{") or content.startswith("[")):
                    try:
                        parsed_content = json.loads(content)
                    except:
                        # If parsing fails, keep the original string
                        pass

                history.append(
                    {
                        "id": id,
                        "timestamp": timestamp,
                        "user": user,
                        "event_type": event_type,
                        "tokens": tokens,
                        "content": parsed_content,
                    }
                )

            return history


# Singleton instance for global access
_logger_instance = None


def get_logger(db_path: str = "chatbot_logs.db") -> EventLogger:
    """Get or create the global logger instance"""
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = EventLogger(db_path)

    return _logger_instance
