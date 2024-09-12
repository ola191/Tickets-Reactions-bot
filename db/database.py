import sqlite3
import datetime

def create_tables(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL UNIQUE,
            prefix TEXT DEFAULT '!',
            admin_role_ids JSON,
            log_channel_id INTEGER,
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
            ticket_category TEXT,
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
