# see eventlogging.py

# log message history

# prompt user that chat is being logged, can run with flag --nolog

# can update db as new messages come in

# chat message logs can be used for:
# - seeing where users need help
# - using chats for additional documents to query
# - estimating costs with tokens per use
# - seeing if there is abuse of system

# can also have mandatory log of token usage, should use better token estimator though

import sqlite3
import os
import time
import json
from datetime import datetime
import uuid

class SQLiteChatLogger:
    """Logger for chatbot conversations using SQLite database"""
    
    def __init__(self, db_path="chat_logs.db"):
        """Initialize logger with database file"""
        self.db_path = db_path
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # Connect to database and create tables if they don't exist
        self._init_database()
        
        # Create a new session
        self._create_session()
        
        # Metrics tracking
        self.metrics = {
            "token_counts": [],
            "response_times": [],
            "tool_uses": 0,
            "retrieval_counts": 0
        }
    
    def _init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            tool_uses INTEGER DEFAULT 0,
            retrieval_count INTEGER DEFAULT 0,
            feedback TEXT
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP,
            role TEXT,
            content TEXT,
            token_count INTEGER,
            response_time REAL,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        # Create events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP,
            event_type TEXT,
            details TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        # Create tool_calls table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tool_calls (
            tool_call_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            message_id INTEGER,
            tool_name TEXT,
            arguments TEXT,
            execution_time REAL,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id),
            FOREIGN KEY (message_id) REFERENCES messages (message_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_session(self):
        """Create a new session in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sessions (session_id, start_time)
        VALUES (?, ?)
        ''', (self.session_id, self.start_time))
        
        conn.commit()
        conn.close()
    
    def log_message(self, message, token_count=None, response_time=None):
        """Log a single message with metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now()
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        # Insert message
        cursor.execute('''
        INSERT INTO messages (session_id, timestamp, role, content, token_count, response_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.session_id, timestamp, role, content, token_count, response_time))
        
        message_id = cursor.lastrowid
        
        # Track metrics
        if token_count:
            self.metrics["token_counts"].append(token_count)
        
        if response_time:
            self.metrics["response_times"].append(response_time)
        
        # Handle tool calls
        if role == "assistant" and message.get("tool_calls"):
            self.metrics["tool_uses"] += 1
            
            for tool_call in message.get("tool_calls", []):
                tool_name = tool_call.get("function", {}).get("name", "unknown")
                arguments = json.dumps(tool_call.get("function", {}).get("arguments", {}))
                
                cursor.execute('''
                INSERT INTO tool_calls (session_id, message_id, tool_name, arguments)
                VALUES (?, ?, ?, ?)
                ''', (self.session_id, message_id, tool_name, arguments))
                
                if tool_name == "retrieve_documents":
                    self.metrics["retrieval_counts"] += 1
        
        # Update session message count
        cursor.execute('''
        UPDATE sessions 
        SET total_messages = total_messages + 1
        WHERE session_id = ?
        ''', (self.session_id,))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def log_event(self, event_type, details):
        """Log non-message events (errors, system events)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now()
        details_json = json.dumps(details) if isinstance(details, dict) else str(details)
        
        cursor.execute('''
        INSERT INTO events (session_id, timestamp, event_type, details)
        VALUES (?, ?, ?, ?)
        ''', (self.session_id, timestamp, event_type, details_json))
        
        conn.commit()
        conn.close()
    
    def update_tool_execution_time(self, message_id, tool_name, execution_time):
        """Update execution time for a tool call"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE tool_calls
        SET execution_time = ?
        WHERE message_id = ? AND tool_name = ?
        ''', (execution_time, message_id, tool_name))
        
        conn.commit()
        conn.close()
    
    def end_session(self, feedback=None):
        """End the logging session with optional feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate metrics for the session
        end_time = datetime.now()
        session_duration = (end_time - self.start_time).total_seconds()
        
        # Get averages
        avg_token_count = sum(self.metrics["token_counts"]) / len(self.metrics["token_counts"]) if self.metrics["token_counts"] else 0
        avg_response_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"]) if self.metrics["response_times"] else 0
        total_tokens = sum(self.metrics["token_counts"])
        
        # Update session with final metrics
        cursor.execute('''
        UPDATE sessions
        SET end_time = ?,
            total_tokens = ?,
            avg_response_time = ?,
            tool_uses = ?,
            retrieval_count = ?,
            feedback = ?
        WHERE session_id = ?
        ''', (end_time, total_tokens, avg_response_time, self.metrics["tool_uses"], 
              self.metrics["retrieval_counts"], feedback, self.session_id))
        
        # Log session end event
        self.log_event("session_ended", {
            "duration_seconds": session_duration,
            "total_messages": len(self.metrics["token_counts"]) + len(self.metrics["response_times"])
        })
        
        conn.commit()
        conn.close()
        
        return self.session_id