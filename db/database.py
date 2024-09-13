import sqlite3
import datetime

import sqlite3
from typing import List, Optional, Tuple

def get_log_channel_id(server_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT log_channel_id FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching log channel ID: {e}")
        return None
    
def fetch_config(server_id: int) -> Optional[Tuple[List[int], Optional[int]]]:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        if result:
            admin_role_ids = eval(result[0]) if result[0] else []
            return (admin_role_ids, result[1])
        return None
    except Exception as e:
        print(f"Error fetching config: {e}")
        return None
    
def connect_db():
    try:
        connection = sqlite3.connect('db/mydatabase.db')
        cursor = connection.cursor()
        return connection, cursor
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None
    
def close_db(connection):
    try:
        connection.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")
        return None
    
def execute_select(query, params=()):
    try:
        connection, cursor = connect_db()
        cursor.execute(query, params)
        result = cursor.fetchall()
        close_db(connection)
        return result
    except Exception as e:
        print(f"Error executing select query: {e}")
        return None
    
def execute_query(query, params=()):
    try:
        connection, cursor = connect_db()
        cursor.execute(query, params)
        connection.commit()
        rowcount = cursor.rowcount
        close_db(connection)
        return rowcount
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    
def generate_ticket_id():
    try:
        connection, cursor = connect_db()
        cursor.execute('SELECT MAX(ticket_id) FROM tickets')
        max_id = cursor.fetchone()[0]
        close_db(connection)
        return (max_id or 0) + 1
    except Exception as e:
        print(f"Error generating ticket ID: {e}")
        return None

def get_db_connection() -> sqlite3.Connection:
    try:
        connection = sqlite3.connect('db/mydatabase.db')
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def fetch_admin_role_ids(server_id: int) -> Optional[List[int]]:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT admin_role_ids FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        return eval(result[0]) if result and result[0] else []
    except Exception as e:
        print(f"Error fetching admin role IDs: {e}")
        return None
    
def fetch_config(server_id: int) -> Optional[Tuple[List[int], Optional[int]]]:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        if result:
            admin_role_ids = eval(result[0]) if result[0] else []
            return (admin_role_ids, result[1])
        return None
    except Exception as e:
        print(f"Error fetching config: {e}")
        return None
    
def insert_config(server_id: int, admin_role_ids: List[int], log_channel_id: Optional[int]):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO config (server_id, admin_role_ids, log_channel_id) VALUES (?, ?, ?)''',
                    (server_id, str(admin_role_ids), log_channel_id))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error inserting config: {e}")
        
def update_config(server_id: int, admin_role_ids: List[int], log_channel_id: Optional[int]):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if log_channel_id is not None:
            cursor.execute('''UPDATE config SET log_channel_id = ? WHERE server_id = ?''',
                        (log_channel_id, server_id))

        if admin_role_ids is not None:
            cursor.execute('''UPDATE config SET admin_role_ids = ? WHERE server_id = ?''',
                        (str(admin_role_ids), server_id))
        
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error updating config: {e}")
        
def add_admin_role(server_id: int, admin_user_id: int):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        admin_roles = fetch_admin_role_ids(server_id)
        if admin_user_id not in admin_roles:
            admin_roles.append(admin_user_id)
            update_config(server_id, admin_roles, None)
        connection.close()
    except Exception as e:
        print(f"Error adding admin role: {e}")
        
def delete_admin_role(server_id: int, admin_user_id: int):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        admin_roles = fetch_admin_role_ids(server_id)
        if admin_user_id in admin_roles:
            admin_roles.remove(admin_user_id)
            update_config(server_id, admin_roles, None)
        connection.close()
    except Exception as e:
        print(f"Error deleting admin role: {e}")
        
def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL UNIQUE,
            prefix TEXT DEFAULT '!',
            admin_role_ids JSON,
            log_channel_id INTEGER,
            other_settings JSON,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            ticket_id INTEGER NOT NULL UNIQUE,
            title TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('open', 'closed', 'in-progress')) DEFAULT 'open',
            priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
            assigned_to INTEGER,
            owner INTEGER,
            comments JSON
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT CHECK(role IN ('admin', 'user')) DEFAULT 'user',
            FOREIGN KEY (ticket_id) REFERENCES tickets(id),
            UNIQUE(ticket_id, user_id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            react_id INTEGER NOT NULL UNIQUE,
            channel_id INTEGER,
            message_id INTEGER,
            react_emoji TEXT,
            react_type TEXT CHECK(react_type IN ('reaction', 'mention')) DEFAULT 'reaction',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(server_id, react_id)
        );
    ''')

async def setup_database(client):
    try:
        conn = sqlite3.connect('db/mydatabase.db')
        cursor = conn.cursor()
        print(f"[{datetime.datetime.now()}] [\033[1;35mCONSOLE\033[0;0m]: Database [\033[1;35mSQLite\033[0;0m] setup.") 

        try:
            for guild in client.guilds:
                create_tables(cursor)
            print(f"[{datetime.datetime.now()}] [\033[1;35mCONSOLE\033[0;0m]: tables [\033[1;35mSQLite\033[0;0m] created.")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] [\033[91mERROR\033[0;0m]: {e}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[{datetime.datetime.now()}] [\033[91mERROR\033[0;0m]: {e}")