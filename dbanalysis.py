# %%
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('chatbot_logs.db')

# %%
def load_all_events():
    query = "SELECT * FROM events ORDER BY timestamp"
    df = pd.read_sql_query(query, conn)
    
    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Try to parse JSON content where possible
    def parse_json_content(content):
        if isinstance(content, str) and (content.startswith('{') or content.startswith('[')):
            try:
                return json.loads(content)
            except:
                pass
        return content
    
    # Leave content as is for display purposes
    return df

events_df = load_all_events()
events_df.head()

# %%
events_df

# %%
def get_chat_sessions():
    query = """
    SELECT chat_uuid, 
           MIN(timestamp) as start_time, 
           MAX(timestamp) as end_time,
           COUNT(*) as event_count
    FROM events 
    GROUP BY chat_uuid
    ORDER BY start_time DESC
    """
    return pd.read_sql_query(query, conn)

sessions_df = get_chat_sessions()
sessions_df.head()

# %%
def analyze_event_types():
    query = """
    SELECT event_type, COUNT(*) as count
    FROM events
    GROUP BY event_type
    ORDER BY count DESC
    """
    return pd.read_sql_query(query, conn)

event_types_df = analyze_event_types()

# Plot event type distribution
plt.figure(figsize=(12, 6))
sns.barplot(x='event_type', y='count', data=event_types_df)
plt.title('Distribution of Event Types')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %%
def analyze_session(chat_uuid):
    # Get all events for this session
    query = f"""
    SELECT * FROM events
    WHERE chat_uuid = ?
    ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, params=(chat_uuid,))
    
    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate time between events
    df['time_delta'] = df['timestamp'].diff().dt.total_seconds()
    
    return df

# Select a chat UUID from the sessions_df
if not sessions_df.empty:
    sample_chat_uuid = sessions_df.iloc[0]['chat_uuid']
    session_events = analyze_session(sample_chat_uuid)
    print(f"Analyzing session: {sample_chat_uuid}")
    print(session_events.head())

# %%
def analyze_response_times():
    # Get all chat sessions
    sessions = get_chat_sessions()
    
    response_times = []
    
    for _, session in sessions.iterrows():
        chat_uuid = session['chat_uuid']
        
        # Get all events for this session
        session_events = analyze_session(chat_uuid)
        
        # Filter for user messages followed by agent responses
        user_msgs = session_events[session_events['event_type'] == 'user_message']
        
        for i, user_msg in user_msgs.iterrows():
            if i+1 < len(session_events) and session_events.iloc[i+1]['event_type'] == 'agent_response':
                agent_response = session_events.iloc[i+1]
                response_time = (agent_response['timestamp'] - user_msg['timestamp']).total_seconds()
                
                response_times.append({
                    'chat_uuid': chat_uuid,
                    'user_message_time': user_msg['timestamp'],
                    'response_time_seconds': response_time
                })
    
    return pd.DataFrame(response_times)

response_times_df = analyze_response_times()

# Plot response time distribution
if not response_times_df.empty:
    plt.figure(figsize=(10, 6))
    sns.histplot(response_times_df['response_time_seconds'], bins=20)
    plt.title('Distribution of Response Times')
    plt.xlabel('Response Time (seconds)')
    plt.tight_layout()
    plt.show()

# %%
def analyze_token_usage():
    query = """
    SELECT date(timestamp) as date, 
           event_type,
           SUM(tokens) as total_tokens
    FROM events
    WHERE tokens IS NOT NULL
    GROUP BY date(timestamp), event_type
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    return df

token_usage_df = analyze_token_usage()

# Plot token usage over time
if not token_usage_df.empty:
    plt.figure(figsize=(14, 7))
    pivot_df = token_usage_df.pivot(index='date', columns='event_type', values='total_tokens')
    pivot_df.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.title('Token Usage by Day and Event Type')
    plt.ylabel('Total Tokens')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# %%
def analyze_tool_calls():
    # Get all tool calls
    query = """
    SELECT * FROM events
    WHERE event_type = 'tool_call'
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    
    # Parse content as JSON
    tool_calls = []
    
    for _, row in df.iterrows():
        content = row['content']
        if isinstance(content, str):
            try:
                content_dict = json.loads(content)
                # Extract tool name if available
                tool_name = content_dict.get('name', 'unknown')
                tool_calls.append({
                    'chat_uuid': row['chat_uuid'],
                    'timestamp': row['timestamp'],
                    'tool_name': tool_name
                })
            except:
                pass
    
    return pd.DataFrame(tool_calls)

tool_calls_df = analyze_tool_calls()

# Show tool usage distribution
if not tool_calls_df.empty:
    plt.figure(figsize=(10, 6))
    sns.countplot(y='tool_name', data=tool_calls_df)
    plt.title('Tool Usage Distribution')
    plt.tight_layout()
    plt.show()

# %%
def analyze_user_activity():
    query = """
    SELECT user, 
           COUNT(*) as message_count,
           COUNT(DISTINCT chat_uuid) as session_count
    FROM events
    WHERE event_type = 'user_message' AND user IS NOT NULL
    GROUP BY user
    ORDER BY message_count DESC
    """
    return pd.read_sql_query(query, conn)

user_activity_df = analyze_user_activity()
user_activity_df.head()

# %%
# Always close the connection when done
conn.close()

# %%


# %%



