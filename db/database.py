import json
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
    
    # -> Optional[Tuple[List[int], Optional[int], List[str]]]
def fetch_config(server_id: int):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT admin_role_ids, log_channel_id, COALESCE(tickets_categories, '[]'), max_tickets_per_user FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        
        # print(f"Fetched result: {result}") 

        if result:
            admin_role_ids = json.loads(result[0]) if result[0] else []
            log_channel_id = result[1]
            categories_names = json.loads(result[2]) if result[2] else []
            max_tickets_per_user = result[3]
            return (admin_role_ids, log_channel_id, categories_names, max_tickets_per_user)
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
    
def insert_config(server_id: int, admin_role_ids: list, log_channel_id: Optional[int]):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO config (server_id, admin_role_ids, log_channel_id) VALUES (?, ?, ?)''',
                    (server_id, str(admin_role_ids), log_channel_id))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error inserting config: {e}")
        
def update_config(server_id: int, admin_role_ids: List[int] = None, log_channel_id: Optional[int] = None, ticket_categories: Optional[List[str]] = None, max_tickets_per_user: Optional[int] = None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if log_channel_id is not None:
            cursor.execute('''UPDATE config SET log_channel_id = ? WHERE server_id = ?''',
                        (log_channel_id, server_id))
        
        admin_role_ids_json = json.dumps(admin_role_ids)
        cursor.execute('''UPDATE config SET admin_role_ids = ? WHERE server_id = ?''',
                    (admin_role_ids_json, server_id))

        if ticket_categories is not None:
            ticket_categories_json = json.dumps(ticket_categories)
            cursor.execute('''UPDATE config SET tickets_categories = ? WHERE server_id = ?''',
                        (ticket_categories_json, server_id))

        if max_tickets_per_user is not None:
            cursor.execute('''UPDATE config SET max_tickets_per_user = ? WHERE server_id = ?''',
                        (max_tickets_per_user, server_id))
            
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
            update_config(server_id, admin_roles, None, None)
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
            update_config(server_id, admin_roles, None, None)
        connection.close()
    except Exception as e:
        print(f"Error deleting admin role: {e}")
        
def fetch_ticket_categories(server_id: int) -> Optional[List[str]]:
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT tickets_categories FROM config WHERE server_id = ?''', (server_id,))
        result = cursor.fetchone()
        connection.close()
        return eval(result[0]) if result and result[0] else []
    except Exception as e:
        print(f"Error fetching ticket categories: {e}")
        return None

def add_ticket_category(server_id: int, category_name: str):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        categories = fetch_ticket_categories(server_id)
        admin_roles = fetch_admin_role_ids(server_id)
        if category_name not in categories:
            categories.append(category_name)
            update_config(server_id, admin_roles, None, categories)
        connection.close()
    except Exception as e:
        print(f"Error adding ticket category: {e}")
        
def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL UNIQUE,
            prefix TEXT DEFAULT '!',
            admin_role_ids JSON,
            log_channel_id INTEGER,
            max_tickets_per_user INTEGER,
            tickets_categories JSON,
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
            category TEXT,
            channel_id INTEGER NOT NULL,
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
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
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