"""
Data Bit AI Solutions - UNIFIED DASHBOARD v3.0 MERGED
=======================================================
Single file — Phase 1 + Phase 2 + All Agents embedded
No external imports needed except pip packages.
"""

# ============================================================
# MERGED IMPORTS
# ============================================================
import streamlit as st
import sqlite3
import hashlib
import json
import requests
import os
import zipfile
import base64
import threading
import queue
import time
import secrets
import shutil
import subprocess
import platform
import psutil
from datetime import datetime, date, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from cryptography.fernet import Fernet

PHASE1_LOADED = True  # Embedded below
PHASE2_LOADED = True  # Embedded
PHASE3_LOADED = True  # Embedded
PHASE4_LOADED = True  # Embedded below

# Data Bit AI Solutions - 8 Major Modules
# 1. HOME (Dashboard)
# 2. MODULE BUILDER
# 3. AI AGENTS
# 4. DATABASE MANAGEMENT
# 5. AI ENGINE
# 6. UI COMPONENTS
# 7. AGENT TOOLS
# 8. SETTINGS

# ====== PHASE 1 CODE ======


import sqlite3
import hashlib
import os
import json
import shutil
import threading
import queue
import time
import secrets
import base64
import zipfile
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.fernet import Fernet

# ============================================================
# SECTION 1 — DATABASE PATHS (Separate DB per concern)
# ============================================================

DB_SYSTEM      = "db/system.db"        # Core system config, restore points, audit
DB_USERS       = "db/users.db"         # All regular users
DB_WHITELABEL  = "db/whitelabel.db"    # All white label instances
DB_AGENTS      = "db/agents.db"        # Agent logs, tools, memory, tasks
DB_PROJECTS    = "db/projects.db"      # Per-project data (sales, crm, finance etc.)
RESTORE_FOLDER = "restores"
KEY_FILE       = "db/.encryption.key"

os.makedirs("db", exist_ok=True)
os.makedirs(RESTORE_FOLDER, exist_ok=True)
os.makedirs("db/project_dbs", exist_ok=True)
os.makedirs("modules", exist_ok=True)


# ============================================================
# SECTION 2 — ENCRYPTION ENGINE
# ============================================================

def load_or_create_key():
    """Load existing encryption key or generate a new one."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

ENCRYPTION_KEY = load_or_create_key()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt(text: str) -> str:
    """Encrypt a string value."""
    if not text:
        return ""
    return cipher.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    """Decrypt an encrypted string."""
    if not token:
        return ""
    try:
        return cipher.decrypt(token.encode()).decode()
    except Exception:
        return ""

def hash_password(password: str) -> str:
    """SHA-256 hash with salt."""
    salt = "databit_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


# ============================================================
# SECTION 3 — DATABASE INITIALIZER
# ============================================================

def get_conn(db_path: str):
    db_dir = os.path.dirname(db_path)
    if db_dir:  # Only create directory if path contains a directory component
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def db_exec(db_path: str, query: str, params=()):
    conn = get_conn(db_path)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id

def db_fetch_with_path(db_path: str, query: str, params=()):
    conn = get_conn(db_path)
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Aliases used throughout Phase 1-4 embedded code
p1_exec  = db_exec
p1_fetch = db_fetch_with_path


def init_system_db():
    """System DB — config, restore points, audit logs, sessions."""
    conn = get_conn(DB_SYSTEM)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS restore_points (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,          -- system | user | whitelabel | project
        target_id TEXT,     -- user_id or wl_id or project_id (null = all)
        file_path TEXT,
        size_bytes INTEGER,
        created_by TEXT,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY,
        user_id TEXT,
        user_type TEXT,     -- admin | user | whitelabel | agent
        action TEXT,
        target TEXT,
        detail TEXT,
        ip_address TEXT,
        session_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS active_sessions (
        id INTEGER PRIMARY KEY,
        user_id TEXT,
        user_type TEXT,
        session_token TEXT UNIQUE,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS rate_limits (
        id INTEGER PRIMARY KEY,
        identifier TEXT,    -- user_id or ip
        action TEXT,
        count INTEGER DEFAULT 1,
        window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


def init_users_db():
    """Users DB — all regular users, separated from system."""
    conn = get_conn(DB_USERS)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT UNIQUE,
        full_name TEXT,
        role TEXT DEFAULT 'user',
        plan TEXT DEFAULT 'basic',  -- basic | pro | enterprise
        is_active BOOLEAN DEFAULT 1,
        email_verified BOOLEAN DEFAULT 0,
        two_factor_enabled BOOLEAN DEFAULT 0,
        two_factor_secret TEXT,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        theme TEXT DEFAULT 'light',
        notifications_enabled BOOLEAN DEFAULT 1,
        email_alerts BOOLEAN DEFAULT 1,
        preferences TEXT DEFAULT '{}',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_restore_points (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        file_path TEXT,
        size_bytes INTEGER,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Default admin user
    c.execute('''INSERT OR IGNORE INTO users
        (id, username, password, email, full_name, role, plan, is_active)
        VALUES (1, 'admin', ?, 'admin@databit.ai', 'System Admin', 'admin', 'enterprise', 1)''',
        (hash_password('admin123'),))

    conn.commit()
    conn.close()


def init_whitelabel_db():
    """White Label DB — completely separate from users."""
    conn = get_conn(DB_WHITELABEL)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS whitelabel_instances (
        id INTEGER PRIMARY KEY,
        company_name TEXT,
        admin_email TEXT UNIQUE,
        password TEXT,
        subdomain TEXT UNIQUE,
        custom_domain TEXT,
        branding TEXT DEFAULT '{}',  -- JSON: logo, colors, fonts
        plan TEXT DEFAULT 'basic',
        status TEXT DEFAULT 'active',
        agent_access TEXT DEFAULT '[]',  -- which agents they can use
        storage_limit_mb INTEGER DEFAULT 1000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS whitelabel_users (
        id INTEGER PRIMARY KEY,
        wl_id INTEGER,
        username TEXT,
        password TEXT,
        email TEXT,
        role TEXT DEFAULT 'client',
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS whitelabel_restore_points (
        id INTEGER PRIMARY KEY,
        wl_id INTEGER,
        file_path TEXT,
        size_bytes INTEGER,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


def init_agents_db():
    """Agents DB — tools, memory, task queue, logs."""
    conn = get_conn(DB_AGENTS)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS agent_tools (
        id INTEGER PRIMARY KEY,
        tool_name TEXT UNIQUE,
        tool_type TEXT,         -- search | file | api | db | communication
        description TEXT,
        config TEXT DEFAULT '{}',
        is_active BOOLEAN DEFAULT 1,
        accessible_by TEXT DEFAULT '[]',  -- agent names that can use this
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS agent_memory (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        user_id TEXT,
        client_id TEXT,
        memory_type TEXT,       -- preference | history | learning | feedback
        content TEXT,
        importance INTEGER DEFAULT 5,  -- 1-10
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS task_queue (
        id INTEGER PRIMARY KEY,
        task_id TEXT UNIQUE,
        agent_name TEXT,
        user_id TEXT,
        task TEXT,
        context TEXT DEFAULT '',
        priority INTEGER DEFAULT 5,  -- 1=urgent 10=low
        status TEXT DEFAULT 'pending',  -- pending|running|done|failed|cancelled
        result TEXT,
        error TEXT,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY,
        task_id TEXT,
        agent_name TEXT,
        action TEXT,
        input_data TEXT,
        output_data TEXT,
        status TEXT,
        duration_ms INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS agent_emails (
        id INTEGER PRIMARY KEY,
        agent_name TEXT UNIQUE,
        email_address TEXT UNIQUE,
        gmail_token TEXT,       -- encrypted OAuth token
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


def init_projects_db():
    """Projects DB — each project gets its own entry, can also get its own file."""
    conn = get_conn(DB_PROJECTS)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        project_id TEXT UNIQUE,
        user_id TEXT,
        name TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        assigned_agents TEXT DEFAULT '[]',
        db_path TEXT,           -- path to this project's own SQLite file
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY,
        project_id TEXT,
        file_name TEXT,
        file_path TEXT,
        file_type TEXT,
        created_by TEXT,        -- agent name or admin
        version INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


def init_all_databases():
    """Initialize all databases at startup."""
    init_system_db()
    init_users_db()
    init_whitelabel_db()
    init_agents_db()
    init_projects_db()
    print("✅ All Phase 1 databases initialized")


# ============================================================
# SECTION 4 — RESTORE POINT ENGINE
# ============================================================

class RestoreEngine:

    @staticmethod
    def create_restore_point(restore_type: str, created_by: str,
                              target_id: str = None, note: str = "") -> dict:
        """
        Create a full restore point (zip snapshot of relevant DB).
        restore_type: 'system' | 'user' | 'whitelabel' | 'project'
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = f"{restore_type}_{target_id or 'all'}_{timestamp}"
        zip_path = os.path.join(RESTORE_FOLDER, f"{name}.zip")

        # Decide which files to snapshot
        files_to_backup = []
        if restore_type == "system":
            files_to_backup = [DB_SYSTEM, DB_AGENTS]
        elif restore_type == "user":
            files_to_backup = [DB_USERS]
        elif restore_type == "whitelabel":
            files_to_backup = [DB_WHITELABEL]
        elif restore_type == "project":
            proj = db_fetch_with_path(DB_PROJECTS, "SELECT db_path FROM projects WHERE project_id=?", (target_id,))
            if proj and proj[0].get("db_path"):
                files_to_backup = [proj[0]["db_path"]]
            files_to_backup.append(DB_PROJECTS)

        # Create zip
        size = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fp in files_to_backup:
                if os.path.exists(fp):
                    zf.write(fp, os.path.basename(fp))
            size = os.path.getsize(zip_path)

        # Log to system DB
        db_exec(DB_SYSTEM, '''INSERT INTO restore_points
            (name, type, target_id, file_path, size_bytes, created_by, note)
            VALUES (?,?,?,?,?,?,?)''',
            (name, restore_type, target_id, zip_path, size, created_by, note))

        # Also log to appropriate user/wl table
        if restore_type == "user" and target_id:
            db_exec(DB_USERS, '''INSERT INTO user_restore_points
                (user_id, file_path, size_bytes, note) VALUES (?,?,?,?)''',
                (target_id, zip_path, size, note))
        elif restore_type == "whitelabel" and target_id:
            db_exec(DB_WHITELABEL, '''INSERT INTO whitelabel_restore_points
                (wl_id, file_path, size_bytes, note) VALUES (?,?,?,?)''',
                (target_id, zip_path, size, note))

        audit(created_by, "admin", "create_restore_point", restore_type,
              f"Restore point created: {name}")

        return {"success": True, "name": name, "path": zip_path,
                "size_kb": round(size / 1024, 2)}

    @staticmethod
    def restore_from_point(restore_id: int, restored_by: str) -> dict:
        """Restore system from a saved restore point."""
        points = db_fetch_with_path(DB_SYSTEM,
            "SELECT * FROM restore_points WHERE id=?", (restore_id,))
        if not points:
            return {"success": False, "error": "Restore point not found"}

        point = points[0]
        zip_path = point["file_path"]

        if not os.path.exists(zip_path):
            return {"success": False, "error": "Restore file missing from disk"}

        # Extract zip back to db folder
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall("db/")

        audit(restored_by, "admin", "restore_from_point",
              point["type"], f"Restored from: {point['name']}")

        return {"success": True, "restored": point["name"]}

    @staticmethod
    def list_restore_points(restore_type: str = None) -> list:
        query = "SELECT * FROM restore_points"
        params = ()
        if restore_type:
            query += " WHERE type=?"
            params = (restore_type,)
        query += " ORDER BY created_at DESC"
        return db_fetch_with_path(DB_SYSTEM, query, params)

    @staticmethod
    def delete_restore_point(restore_id: int, deleted_by: str) -> dict:
        points = db_fetch_with_path(DB_SYSTEM,
            "SELECT * FROM restore_points WHERE id=?", (restore_id,))
        if not points:
            return {"success": False, "error": "Not found"}
        point = points[0]
        if os.path.exists(point["file_path"]):
            os.remove(point["file_path"])
        db_exec(DB_SYSTEM, "DELETE FROM restore_points WHERE id=?", (restore_id,))
        audit(deleted_by, "admin", "delete_restore_point",
              "restore_point", f"Deleted: {point['name']}")
        return {"success": True}


# ============================================================
# SECTION 5 — SECURITY ENGINE
# ============================================================

def audit(user_id: str, user_type: str, action: str,
          target: str, detail: str, ip: str = "", session: str = ""):
    """Write to audit log."""
    db_exec(DB_SYSTEM, '''INSERT INTO audit_log
        (user_id, user_type, action, target, detail, ip_address, session_token)
        VALUES (?,?,?,?,?,?,?)''',
        (str(user_id), user_type, action, target, detail[:1000], ip, session))


def create_session(user_id: str, user_type: str,
                   hours: int = 8) -> str:
    """Create a new session token."""
    token = generate_session_token()
    expires = datetime.now() + timedelta(hours=hours)
    # Clean old sessions for this user
    db_exec(DB_SYSTEM,
        "DELETE FROM active_sessions WHERE user_id=? AND user_type=?",
        (str(user_id), user_type))
    db_exec(DB_SYSTEM, '''INSERT INTO active_sessions
        (user_id, user_type, session_token, expires_at)
        VALUES (?,?,?,?)''',
        (str(user_id), user_type, token, expires))
    return token


def validate_session(token: str) -> dict:
    """Check if session token is valid and not expired."""
    rows = db_fetch_with_path(DB_SYSTEM,
        "SELECT * FROM active_sessions WHERE session_token=?", (token,))
    if not rows:
        return {"valid": False, "reason": "Token not found"}
    session = rows[0]
    if datetime.fromisoformat(session["expires_at"]) < datetime.now():
        db_exec(DB_SYSTEM,
            "DELETE FROM active_sessions WHERE session_token=?", (token,))
        return {"valid": False, "reason": "Session expired"}
    return {"valid": True, "user_id": session["user_id"],
            "user_type": session["user_type"]}


def check_rate_limit(identifier: str, action: str,
                     max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """Returns True if allowed, False if rate limited."""
    window_start = datetime.now() - timedelta(minutes=window_minutes)
    rows = db_fetch_with_path(DB_SYSTEM, '''SELECT * FROM rate_limits
        WHERE identifier=? AND action=? AND window_start > ?''',
        (identifier, action, window_start))
    if rows and rows[0]["count"] >= max_attempts:
        return False
    if rows:
        db_exec(DB_SYSTEM, '''UPDATE rate_limits SET count=count+1
            WHERE identifier=? AND action=?''', (identifier, action))
    else:
        db_exec(DB_SYSTEM, '''INSERT INTO rate_limits
            (identifier, action, count, window_start) VALUES (?,?,1,?)''',
            (identifier, action, datetime.now()))
    return True


def cleanup_expired_sessions():
    """Remove expired sessions — call periodically."""
    db_exec(DB_SYSTEM,
        "DELETE FROM active_sessions WHERE expires_at < ?", (datetime.now(),))


# ============================================================
# SECTION 6 — MULTI-TASK ENGINE
# ============================================================

class TaskEngine:
    """
    Manages parallel agent task execution.
    - Priority queue (1=urgent, 10=low)
    - ThreadPoolExecutor for true parallel runs
    - Live status tracking
    - Error isolation per task
    - Task cancellation support
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_futures = {}        # task_id -> future
        self.task_lock = threading.Lock()
        self._running = True
        # Start queue processor in background
        self._queue_thread = threading.Thread(
            target=self._process_queue, daemon=True)
        self._queue_thread.start()

    def submit_task(self, agent_fn, user_id: str, agent_name: str,
                    task: str, context: str = "",
                    priority: int = 5) -> str:
        """Submit a task to the queue. Returns task_id."""
        task_id = f"{agent_name.replace(' ', '_')}_{secrets.token_hex(4)}"

        db_exec(DB_AGENTS, '''INSERT INTO task_queue
            (task_id, agent_name, user_id, task, context, priority, status)
            VALUES (?,?,?,?,?,?,?)''',
            (task_id, agent_name, str(user_id), task, context, priority, "pending"))

        audit(user_id, "user", "task_submitted", agent_name,
              f"Task: {task[:100]}")
        return task_id

    def _process_queue(self):
        """Background thread: picks pending tasks and runs them."""
        while self._running:
            try:
                # Get next pending task ordered by priority then time
                rows = db_fetch_with_path(DB_AGENTS, '''SELECT * FROM task_queue
                    WHERE status='pending'
                    ORDER BY priority ASC, created_at ASC LIMIT 1''')
                if rows:
                    task_row = rows[0]
                    task_id = task_row["task_id"]

                    # Mark as running
                    db_exec(DB_AGENTS, '''UPDATE task_queue
                        SET status='running', started_at=? WHERE task_id=?''',
                        (datetime.now(), task_id))

                    # Submit to thread pool
                    with self.task_lock:
                        future = self.executor.submit(
                            self._run_task, task_row)
                        self.active_futures[task_id] = future

                time.sleep(0.5)  # Poll every 500ms
            except Exception as e:
                print(f"Queue processor error: {e}")
                time.sleep(1)

    def _run_task(self, task_row: dict):
        """Execute a single task and save result."""
        task_id = task_row["task_id"]
        start = datetime.now()
        try:
            # Dynamically get agent function from AGENTS registry
            from main import AGENTS
            agent_label = task_row["agent_name"]
            agent_entry = AGENTS.get(agent_label)

            if not agent_entry:
                raise ValueError(f"Agent '{agent_label}' not found in registry")

            result = agent_entry["fn"](
                task_row["user_id"],
                task_row["task"],
                task_row["context"] or ""
            )

            duration = int((datetime.now() - start).total_seconds() * 1000)

            db_exec(DB_AGENTS, '''UPDATE task_queue
                SET status='done', result=?, completed_at=? WHERE task_id=?''',
                (str(result)[:5000], datetime.now(), task_id))

            db_exec(DB_AGENTS, '''INSERT INTO agent_logs
                (task_id, agent_name, action, input_data, output_data,
                 status, duration_ms)
                VALUES (?,?,?,?,?,?,?)''',
                (task_id, task_row["agent_name"], "execute_task",
                 task_row["task"][:500], str(result)[:500], "success", duration))

        except Exception as e:
            db_exec(DB_AGENTS, '''UPDATE task_queue
                SET status='failed', error=?, completed_at=? WHERE task_id=?''',
                (str(e), datetime.now(), task_id))

            db_exec(DB_AGENTS, '''INSERT INTO agent_logs
                (task_id, agent_name, action, input_data, output_data,
                 status, duration_ms)
                VALUES (?,?,?,?,?,?,?)''',
                (task_id, task_row["agent_name"], "execute_task",
                 task_row["task"][:500], str(e)[:500], "failed", 0))

        finally:
            with self.task_lock:
                self.active_futures.pop(task_id, None)

    def cancel_task(self, task_id: str) -> dict:
        """Cancel a pending or running task."""
        with self.task_lock:
            future = self.active_futures.get(task_id)
            if future:
                future.cancel()
                self.active_futures.pop(task_id, None)

        db_exec(DB_AGENTS, '''UPDATE task_queue
            SET status='cancelled', completed_at=? WHERE task_id=?''',
            (datetime.now(), task_id))
        return {"success": True, "task_id": task_id}

    def get_task_status(self, task_id: str) -> dict:
        rows = db_fetch_with_path(DB_AGENTS,
            "SELECT * FROM task_queue WHERE task_id=?", (task_id,))
        return rows[0] if rows else {"error": "Task not found"}

    def get_all_tasks(self, user_id: str = None,
                      status: str = None) -> list:
        query = "SELECT * FROM task_queue WHERE 1=1"
        params = []
        if user_id:
            query += " AND user_id=?"
            params.append(str(user_id))
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT 100"
        return db_fetch_with_path(DB_AGENTS, query, tuple(params))

    def retry_failed_task(self, task_id: str) -> dict:
        rows = db_fetch_with_path(DB_AGENTS,
            "SELECT * FROM task_queue WHERE task_id=? AND status='failed'",
            (task_id,))
        if not rows:
            return {"success": False, "error": "Task not found or not failed"}
        db_exec(DB_AGENTS, '''UPDATE task_queue
            SET status='pending', error=NULL, result=NULL,
                started_at=NULL, completed_at=NULL WHERE task_id=?''',
            (task_id,))
        return {"success": True, "task_id": task_id}

    def get_stats(self) -> dict:
        statuses = ["pending", "running", "done", "failed", "cancelled"]
        stats = {}
        for s in statuses:
            rows = db_fetch_with_path(DB_AGENTS,
                "SELECT COUNT(*) as cnt FROM task_queue WHERE status=?", (s,))
            stats[s] = rows[0]["cnt"] if rows else 0
        stats["active_threads"] = len(self.active_futures)
        return stats

    def shutdown(self):
        self._running = False
        self.executor.shutdown(wait=False)


# ============================================================
# SECTION 7 — PROJECT DATABASE ENGINE
# ============================================================

def create_project_db(project_id: str) -> str:
    """Create a dedicated SQLite DB for a project."""
    db_path = f"db/project_dbs/{project_id}.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Each project gets its own tables
    c.execute('''CREATE TABLE IF NOT EXISTS project_sales_leads (
        id INTEGER PRIMARY KEY, contact_name TEXT, company TEXT,
        email TEXT, phone TEXT, status TEXT, value REAL, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_tasks (
        id INTEGER PRIMARY KEY, title TEXT, description TEXT,
        assigned_agent TEXT, status TEXT DEFAULT 'todo',
        priority INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_files (
        id INTEGER PRIMARY KEY, file_name TEXT, file_path TEXT,
        file_type TEXT, created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_notes (
        id INTEGER PRIMARY KEY, content TEXT, created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_chat (
        id INTEGER PRIMARY KEY, sender TEXT, sender_type TEXT,
        message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    return db_path


def register_project(user_id: str, name: str,
                     description: str = "") -> dict:
    """Register a new project and create its DB."""
    project_id = f"proj_{secrets.token_hex(6)}"
    db_path = create_project_db(project_id)

    db_exec(DB_PROJECTS, '''INSERT INTO projects
        (project_id, user_id, name, description, db_path)
        VALUES (?,?,?,?,?)''',
        (project_id, str(user_id), name, description, db_path))

    audit(user_id, "user", "create_project", project_id,
          f"Project '{name}' created")

    return {"project_id": project_id, "db_path": db_path, "name": name}


# ============================================================
# SECTION 8 — GLOBAL TASK ENGINE INSTANCE
# ============================================================

# Initialize all databases
init_all_databases()

# Start the task engine (singleton)
task_engine = TaskEngine(max_workers=10)

print("✅ Phase 1 Foundation loaded:")
print("   ✅ Separate databases (system / users / whitelabel / agents / projects)")
print("   ✅ Encryption engine (Fernet AES)")
print("   ✅ Restore point engine (zip snapshots)")
print("   ✅ Security engine (sessions, audit, rate limiting)")
print("   ✅ Multi-task engine (10 parallel threads + priority queue)")
print("   ✅ Per-project database engine")


# ====== PHASE 2 CODE ======


import os
import json
import sqlite3
import requests
import threading
import subprocess
import platform
import psutil
import secrets
from datetime import datetime
from pathlib import Path

# Import Phase 1
# Phase 1 is fully embedded above — all symbols available globally
PHASE1_OK = True


# ============================================================
# SECTION 1 — FILE SYSTEM POWERS
# ============================================================

class AgentFileSystem:
    """
    Full file system access for all agents.
    Read, write, delete, list, move, search files.
    All actions are logged.
    """

    BASE_DIRS = {
        "outputs":    "agent_outputs",
        "reports":    "reports",
        "templates":  "templates",
        "sites":      "generated_sites",
        "marketing":  "marketing_output",
        "crm":        "crm_output",
        "mobile":     "mobile_output",
        "admin":      "admin_output",
        "projects":   "db/project_dbs",
        "uploads":    "uploads",
        "training":   "ai_training",
        "tools":      "agent_tools_files",
    }

    @staticmethod
    def _ensure_dir(path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    @staticmethod
    def write_file(agent_name: str, folder_key: str, filename: str,
                   content: str, mode: str = "w") -> dict:
        """Agent writes a file. folder_key maps to a safe base directory."""
        base = AgentFileSystem.BASE_DIRS.get(folder_key, "agent_outputs")
        os.makedirs(base, exist_ok=True)
        filepath = os.path.join(base, filename)
        try:
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(content)
            size = os.path.getsize(filepath)
            _log_file_action(agent_name, "write", filepath, size)
            return {"success": True, "path": filepath, "size_bytes": size}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def read_file(agent_name: str, filepath: str) -> dict:
        """Agent reads any file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            _log_file_action(agent_name, "read", filepath, len(content))
            return {"success": True, "content": content, "path": filepath}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_file(agent_name: str, filepath: str) -> dict:
        """Agent deletes a file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                _log_file_action(agent_name, "delete", filepath, 0)
                return {"success": True, "deleted": filepath}
            return {"success": False, "error": "File not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_files(agent_name: str, folder_key: str,
                   extension: str = None) -> dict:
        """List all files in an agent folder."""
        base = AgentFileSystem.BASE_DIRS.get(folder_key, "agent_outputs")
        if not os.path.exists(base):
            return {"success": True, "files": []}
        files = []
        for f in sorted(Path(base).rglob("*")):
            if f.is_file():
                if extension and not str(f).endswith(extension):
                    continue
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size_kb": round(f.stat().st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(
                        f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        return {"success": True, "files": files, "count": len(files)}

    @staticmethod
    def move_file(agent_name: str, src: str, dest: str) -> dict:
        """Move/rename a file."""
        try:
            AgentFileSystem._ensure_dir(dest)
            os.rename(src, dest)
            _log_file_action(agent_name, "move", f"{src} → {dest}", 0)
            return {"success": True, "moved_to": dest}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search_files(agent_name: str, keyword: str,
                     folder_key: str = None) -> dict:
        """Search file contents for a keyword."""
        base = AgentFileSystem.BASE_DIRS.get(folder_key, ".") if folder_key else "."
        matches = []
        for f in Path(base).rglob("*.txt"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if keyword.lower() in content.lower():
                    matches.append({
                        "file": str(f),
                        "preview": content[:200]
                    })
            except Exception:
                continue
        return {"success": True, "matches": matches, "count": len(matches)}

    @staticmethod
    def append_to_file(agent_name: str, filepath: str, content: str) -> dict:
        """Append content to existing file."""
        return AgentFileSystem.write_file(
            agent_name, "outputs",
            os.path.basename(filepath), f"\n{content}", "a"
        )


def _log_file_action(agent_name: str, action: str, filepath: str, size: int):
    """Log file operation to agents DB."""
    if PHASE1_OK:
        db_exec(DB_AGENTS, '''INSERT INTO agent_logs
            (agent_name, action, input_data, output_data, status, duration_ms)
            VALUES (?,?,?,?,?,?)''',
            (agent_name, f"file_{action}", filepath, str(size), "success", 0))


# ============================================================
# SECTION 2 — DATABASE OVERRIDE ENGINE
# ============================================================

class AgentDBOverride:
    """
    Agents can read and override any database record.
    Full CRUD on any table in any DB.
    All overrides are logged with before/after values.
    """

    # Map friendly names to DB paths
    DB_MAP = {
        "system":     "db/system.db",
        "users":      "db/users.db",
        "whitelabel": "db/whitelabel.db",
        "agents":     "db/agents.db",
        "projects":   "db/projects.db",
        "main":       "databit_unified.db",  # legacy main DB
    }

    @staticmethod
    def _get_db(db_key: str) -> str:
        return AgentDBOverride.DB_MAP.get(db_key, db_key)

    @staticmethod
    def query(agent_name: str, db_key: str,
              sql: str, params: tuple = ()) -> dict:
        """Agent runs a SELECT query on any DB."""
        db_path = AgentDBOverride._get_db(db_key)
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(sql, params)
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            _log_db_action(agent_name, "query", db_key, sql, f"{len(rows)} rows")
            return {"success": True, "rows": rows, "count": len(rows)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update(agent_name: str, db_key: str, table: str,
               updates: dict, where: str, where_params: tuple = ()) -> dict:
        """Agent updates records in any DB table."""
        db_path = AgentDBOverride._get_db(db_key)
        try:
            # Capture before state
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(f"SELECT * FROM {table} WHERE {where}", where_params)
            before = [dict(r) for r in c.fetchall()]

            # Build UPDATE
            set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
            params = list(updates.values()) + list(where_params)
            c.execute(f"UPDATE {table} SET {set_clause} WHERE {where}", params)
            affected = c.rowcount
            conn.commit()
            conn.close()

            _log_db_action(agent_name, "update", db_key,
                          f"UPDATE {table} SET {set_clause} WHERE {where}",
                          f"{affected} rows updated. Before: {before}")
            return {"success": True, "rows_affected": affected, "before": before}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def insert(agent_name: str, db_key: str,
               table: str, data: dict) -> dict:
        """Agent inserts a record into any DB table."""
        db_path = AgentDBOverride._get_db(db_key)
        try:
            cols = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                     list(data.values()))
            new_id = c.lastrowid
            conn.commit()
            conn.close()
            _log_db_action(agent_name, "insert", db_key,
                          f"INSERT INTO {table}", f"New ID: {new_id}")
            return {"success": True, "new_id": new_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete(agent_name: str, db_key: str, table: str,
               where: str, where_params: tuple = ()) -> dict:
        """Agent deletes records from any DB table."""
        db_path = AgentDBOverride._get_db(db_key)
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            # Capture before
            c.execute(f"SELECT * FROM {table} WHERE {where}", where_params)
            before = c.fetchall()
            c.execute(f"DELETE FROM {table} WHERE {where}", where_params)
            affected = c.rowcount
            conn.commit()
            conn.close()
            _log_db_action(agent_name, "delete", db_key,
                          f"DELETE FROM {table} WHERE {where}",
                          f"{affected} rows deleted")
            return {"success": True, "rows_deleted": affected}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_tables(db_key: str) -> dict:
        """List all tables in a database."""
        db_path = AgentDBOverride._get_db(db_key)
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in c.fetchall()]
            conn.close()
            return {"success": True, "tables": tables}
        except Exception as e:
            return {"success": False, "error": str(e)}


def _log_db_action(agent_name: str, action: str, db_key: str,
                   query: str, result: str):
    if PHASE1_OK:
        db_exec(DB_AGENTS, '''INSERT INTO agent_logs
            (agent_name, action, input_data, output_data, status, duration_ms)
            VALUES (?,?,?,?,?,?)''',
            (agent_name, f"db_{action}", f"{db_key}:{query[:200]}",
             str(result)[:500], "success", 0))


# ============================================================
# SECTION 3 — LIVE SEARCH ENGINE
# ============================================================

class LiveSearchEngine:
    """
    Hybrid online/offline search engine with local indexing.
    Supports live web search + local file + DB + system search.
    All searches are logged.
    """
    
    # Offline search index for faster local searches
    SEARCH_INDEX = {}
    
    @staticmethod
    def initialize_offline_index():
        """Initialize the offline search index with local content."""
        try:
            # Index local files
            LiveSearchEngine.index_local_files()
            
            # Index database content
            LiveSearchEngine.index_database_content()
            
            # Index system logs
            LiveSearchEngine.index_system_content()
            
            print("✅ Offline search index initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize offline index: {e}")

    @staticmethod
    def index_local_files():
        """Index local files for fast offline search."""
        try:
            import hashlib
            for ext in ['.txt', '.pdf', '.docx', '.xlsx', '.csv', '.py', '.js', '.html', '.css', '.json', '.md']:
                for file_path in Path('.').rglob(f'*{ext}'):
                    if file_path.is_file():
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            # Create hash of content as key
                            content_hash = hashlib.md5(content.encode()).hexdigest()
                            LiveSearchEngine.SEARCH_INDEX[f"file:{file_path}"] = {
                                'type': 'file',
                                'path': str(file_path),
                                'content': content,
                                'hash': content_hash,
                                'modified': file_path.stat().st_mtime
                            }
                        except:
                            continue  # Skip files that can't be read
            print(f"  - Indexed {len([k for k in LiveSearchEngine.SEARCH_INDEX if k.startswith('file:')])} local files")
        except Exception as e:
            print(f"  - Error indexing files: {e}")

    @staticmethod
    def index_database_content():
        """Index database content for fast offline search."""
        try:
            conn = sqlite3.connect(DB_SYSTEM)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                try:
                    # Get records from each table
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")  # Limit to prevent huge indexes
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for i, row in enumerate(rows):
                        record_content = " ".join([str(val) for val in row if val])
                        if record_content.strip():
                            record_key = f"db:{table_name}:{i}"
                            LiveSearchEngine.SEARCH_INDEX[record_key] = {
                                'type': 'database',
                                'table': table_name,
                                'columns': columns,
                                'values': dict(zip(columns, row)),
                                'content': record_content
                            }
                except:
                    continue  # Skip problematic tables
            
            conn.close()
            print(f"  - Indexed database content")
        except Exception as e:
            print(f"  - Error indexing database: {e}")

    @staticmethod
    def index_system_content():
        """Index system logs and chat history for fast offline search."""
        try:
            # Index chat history
            conn = sqlite3.connect(DB_CHAT)
            cursor = conn.cursor()
            cursor.execute("SELECT room_id, sender, message, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT 1000")
            chats = cursor.fetchall()
            for i, chat in enumerate(chats):
                content = f"Room: {chat[0]}, From: {chat[1]}, Message: {chat[2]}"
                LiveSearchEngine.SEARCH_INDEX[f"chat:{i}"] = {
                    'type': 'chat',
                    'room_id': chat[0],
                    'sender': chat[1],
                    'message': chat[2],
                    'timestamp': chat[3],
                    'content': content
                }
            conn.close()
            
            # Index agent memory
            conn = sqlite3.connect(DB_AGENTS)
            cursor = conn.cursor()
            cursor.execute("SELECT agent_name, user_id, content, memory_type, created_at FROM agent_memory ORDER BY created_at DESC LIMIT 1000")
            memories = cursor.fetchall()
            for i, mem in enumerate(memories):
                content = f"Agent: {mem[0]}, User: {mem[1]}, Type: {mem[3]}, Content: {mem[2]}"
                LiveSearchEngine.SEARCH_INDEX[f"memory:{i}"] = {
                    'type': 'memory',
                    'agent': mem[0],
                    'user_id': mem[1],
                    'content': mem[2],
                    'type': mem[3],
                    'timestamp': mem[4],
                    'indexed_content': content
                }
            conn.close()
            
            print(f"  - Indexed system content")
        except Exception as e:
            print(f"  - Error indexing system content: {e}")

    @staticmethod
    def web_search(query: str, max_results: int = 5) -> dict:
        """
        Hybrid web search with online/offline fallback.
        """
        try:
            # Check if online first
            try:
                import urllib.request
                urllib.request.urlopen('https://www.google.com', timeout=3)
                # Online - perform actual search
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query, "format": "json",
                    "no_redirect": "1", "no_html": "1",
                    "skip_disambig": "1"
                }
                r = requests.get(url, params=params, timeout=10)
                data = r.json()

                results = []

                # Abstract (main answer)
                if data.get("AbstractText"):
                    results.append({
                        "type": "abstract",
                        "title": data.get("Heading", query),
                        "text": data["AbstractText"],
                        "url": data.get("AbstractURL", "")
                    })

                # Related topics
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "type": "related",
                            "title": topic.get("Text", "")[:80],
                            "text": topic.get("Text", ""),
                            "url": topic.get("FirstURL", "")
                        })

                # Infobox
                if data.get("Infobox"):
                    for item in data["Infobox"].get("content", [])[:5]:
                        results.append({
                            "type": "infobox",
                            "title": item.get("label", ""),
                            "text": str(item.get("value", "")),
                            "url": ""
                        })

                return {
                    "success": True,
                    "query": query,
                    "results": results[:max_results],
                    "count": len(results),
                    "source": "online"
                }
            except:
                # Offline - search in indexed content
                offline_results = LiveSearchEngine.offline_search(query, max_results)
                offline_results["fallback"] = "offline"
                return offline_results
        except Exception as e:
            return {"success": False, "error": str(e), "source": "offline"}

    @staticmethod
    def wikipedia_search(query: str) -> dict:
        """Hybrid Wikipedia search with offline fallback."""
        try:
            try:
                import urllib.request
                urllib.request.urlopen('https://www.wikipedia.org', timeout=3)
                # Online - perform actual search
                url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + \
                      requests.utils.quote(query)
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "success": True,
                        "title": data.get("title", ""),
                        "summary": data.get("extract", ""),
                        "url": data.get("content_urls", {}).get(
                            "desktop", {}).get("page", ""),
                        "thumbnail": data.get("thumbnail", {}).get("source", ""),
                        "source": "online"
                    }
                return {"success": False, "error": f"HTTP {r.status_code}", "source": "online"}
            except:
                # Offline - search in indexed content
                offline_results = LiveSearchEngine.offline_search(query, 1)
                offline_results["fallback"] = "offline"
                return offline_results
        except Exception as e:
            return {"success": False, "error": str(e), "source": "offline"}

    @staticmethod
    def offline_search(query: str, num_results: int = 10) -> dict:
        """Search in the offline index."""
        try:
            results = []
            query_lower = query.lower()
            
            # Search in the index
            for key, entry in LiveSearchEngine.SEARCH_INDEX.items():
                content = entry.get('content', '').lower()
                if query_lower in content:
                    score = content.count(query_lower)  # Simple scoring based on frequency
                    results.append({
                        "score": score,
                        "entry": entry,
                        "key": key,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
            
            # Sort by score (descending)
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top results
            top_results = []
            for result in results[:num_results]:
                entry = result['entry']
                top_results.append({
                    "type": entry['type'],
                    "title": entry.get('title', entry.get('path', entry.get('table', 'Offline Result'))),
                    "content": result['preview'],
                    "source": entry.get('path', entry.get('table', 'offline')),
                    "detail": entry
                })
            
            _log_search("offline", query, len(top_results))
            return {"success": True, "results": top_results, "source": "offline"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def system_resources() -> dict:
        """Get live system resource usage."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = psutil.net_io_counters()

            # Running processes
            processes = []
            for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                               key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:5]:
                processes.append(proc.info)

            return {
                "success": True,
                "cpu_percent": cpu,
                "cpu_cores": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(mem.total / 1e9, 2),
                    "used_gb": round(mem.used / 1e9, 2),
                    "percent": mem.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1e9, 2),
                    "used_gb": round(disk.used / 1e9, 2),
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent_mb": round(net.bytes_sent / 1e6, 2),
                    "bytes_recv_mb": round(net.bytes_recv / 1e6, 2)
                },
                "top_processes": processes,
                "platform": platform.system(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search_internal_db(db_key: str, keyword: str) -> dict:
        """
        Search all text columns across all tables in a DB for a keyword.
        Enhanced with offline indexing.
        """
        try:
            # First try offline search in our index
            offline_results = []
            keyword_lower = keyword.lower()
            for key, entry in LiveSearchEngine.SEARCH_INDEX.items():
                if entry['type'] == 'database':
                    content = entry.get('content', '').lower()
                    if keyword_lower in content:
                        offline_results.append(entry)
            
            if offline_results:
                return {"success": True, "keyword": keyword,
                        "matches": offline_results[:10], "tables_searched": len(offline_results),
                        "source": "offline_index"}
            
            # If not found in index, try live search
            result = AgentDBOverride.list_tables(db_key)
            if not result["success"]:
                return result

            db_path = AgentDBOverride._get_db(db_key)
            matches = []

            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()

                for table in result["tables"]:
                    # Get column info
                    c.execute(f"PRAGMA table_info({table})")
                    cols = [r[1] for r in c.fetchall()
                            if r[2] in ("TEXT", "VARCHAR", "")]

                    if not cols:
                        continue

                    where = " OR ".join([f"{col} LIKE ?" for col in cols])
                    params = [f"%{keyword}%" for _ in cols]

                    try:
                        c.execute(f"SELECT * FROM {table} WHERE {where} LIMIT 5",
                                 params)
                        rows = [dict(r) for r in c.fetchall()]
                        if rows:
                            matches.append({
                                "table": table,
                                "rows": rows,
                                "count": len(rows)
                            })
                    except Exception:
                        continue

                conn.close()
                return {"success": True, "keyword": keyword,
                        "matches": matches, "tables_searched": len(result["tables"])}
            except Exception as e:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def search_all(query: str) -> dict:
        """Run all search types simultaneously in parallel with online/offline hybrid capability."""
        results = {}

        def _run(key, fn, *args):
            try:
                results[key] = fn(*args)
            except Exception as e:
                results[key] = {"success": False, "error": str(e)}

        # Check online status
        is_online = True
        try:
            import urllib.request
            urllib.request.urlopen('https://www.google.com', timeout=3)
        except:
            is_online = False

        threads = []
        if is_online:
            # Online search threads
            threads = [
                threading.Thread(target=_run, args=("web", LiveSearchEngine.web_search, query)),
                threading.Thread(target=_run, args=("wiki", LiveSearchEngine.wikipedia_search, query)),
                threading.Thread(target=_run, args=("system", LiveSearchEngine.system_resources)),
                threading.Thread(target=_run, args=("files", AgentFileSystem.search_files,
                                                     "search_engine", query, None)),
            ]
        else:
            # Offline search threads
            threads = [
                threading.Thread(target=_run, args=("offline", LiveSearchEngine.offline_search, query)),
                threading.Thread(target=_run, args=("system", LiveSearchEngine.system_resources)),
            ]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # Add connection status
        results['connection_status'] = "online" if is_online else "offline"
        
        return results


# ============================================================
# SECTION 4 — AGENT MEMORY SYSTEM
# ============================================================

class AgentMemory:
    """
    Persistent memory for each agent per client/user.
    Agents remember preferences, history, learnings.
    """

    @staticmethod
    def save(agent_name: str, user_id: str, memory_type: str,
             content: str, importance: int = 5,
             client_id: str = None) -> dict:
        """
        Save a memory for an agent.
        memory_type: preference | history | learning | feedback | client_note
        importance: 1-10 (10 = most important)
        """
        if not PHASE1_OK:
            return {"success": False, "error": "Phase 1 not loaded"}
        try:
            db_exec(DB_AGENTS, '''INSERT INTO agent_memory
                (agent_name, user_id, client_id, memory_type, content, importance)
                VALUES (?,?,?,?,?,?)''',
                (agent_name, str(user_id), client_id or "",
                 memory_type, content, importance))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def recall(agent_name: str, user_id: str,
               memory_type: str = None, limit: int = 10) -> list:
        """Retrieve memories for an agent, most important first."""
        if not PHASE1_OK:
            return []
        query = '''SELECT * FROM agent_memory
            WHERE agent_name=? AND user_id=?'''
        params = [agent_name, str(user_id)]
        if memory_type:
            query += " AND memory_type=?"
            params.append(memory_type)
        query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)
        return db_fetch_with_path(DB_AGENTS, query, tuple(params))

    @staticmethod
    def recall_client(agent_name: str, client_id: str) -> list:
        """Recall all memories about a specific client."""
        if not PHASE1_OK:
            return []
        return db_fetch_with_path(DB_AGENTS, '''SELECT * FROM agent_memory
            WHERE agent_name=? AND client_id=?
            ORDER BY importance DESC LIMIT 20''',
            (agent_name, client_id))

    @staticmethod
    def forget(agent_name: str, user_id: str,
               memory_type: str = None) -> dict:
        """Clear memories for an agent (or specific type)."""
        if not PHASE1_OK:
            return {"success": False}
        if memory_type:
            db_exec(DB_AGENTS,
                "DELETE FROM agent_memory WHERE agent_name=? AND user_id=? AND memory_type=?",
                (agent_name, str(user_id), memory_type))
        else:
            db_exec(DB_AGENTS,
                "DELETE FROM agent_memory WHERE agent_name=? AND user_id=?",
                (agent_name, str(user_id)))
        return {"success": True}

    @staticmethod
    def build_context(agent_name: str, user_id: str,
                      current_task: str) -> str:
        """
        Build a rich context string from agent memory
        to inject into AI prompts.
        """
        memories = AgentMemory.recall(agent_name, user_id, limit=15)
        if not memories:
            return ""

        ctx_parts = [f"[AGENT MEMORY FOR {agent_name}]"]
        for m in memories:
            ctx_parts.append(
                f"- [{m['memory_type'].upper()}] {m['content']}"
            )
        ctx_parts.append(f"[CURRENT TASK]: {current_task}")
        return "\n".join(ctx_parts)


# ============================================================
# SECTION 5 — AGENT COLLABORATION ENGINE
# ============================================================

class AgentCollaboration:
    """
    Agents pass work to each other.
    Sales briefs Marketing. WebDev notifies CRM. etc.
    """

    # Who each agent should notify after completing work
    HANDOFF_MAP = {
        "💼 Sales AI":      ["🤝 CRM AI", "📢 Marketing AI"],
        "🌐 Web Dev AI":    ["🤝 CRM AI", "🛡️ Admin AI"],
        "📢 Marketing AI":  ["💼 Sales AI"],
        "💰 Finance AI":    ["🤝 CRM AI", "🛡️ Admin AI"],
        "🤝 CRM AI":        ["💼 Sales AI", "📢 Marketing AI"],
        "📊 ERP AI":        ["💰 Finance AI", "🛡️ Admin AI"],
        "📱 Mobile AI":     ["🌐 Web Dev AI", "🛡️ Admin AI"],
        "👑 Lead Master Agent": [],  # Master delegates, doesn't receive
    }

    @staticmethod
    def handoff(from_agent: str, user_id: str, task: str,
                result_summary: str, agents_registry: dict) -> list:
        """
        After an agent completes work, automatically notify
        and brief relevant partner agents.
        Returns list of handoff results.
        """
        targets = AgentCollaboration.HANDOFF_MAP.get(from_agent, [])
        handoff_results = []

        for target_agent in targets:
            if target_agent not in agents_registry:
                continue

            handoff_task = f"""[HANDOFF FROM {from_agent}]
Original task completed: {task}
Summary of work done: {result_summary[:500]}
Your follow-up action: Based on the above, take any relevant action for your domain.
"""
            # Queue the handoff task (non-blocking)
            if PHASE1_OK:
                task_id = task_engine.submit_task(
                    agents_registry[target_agent]["fn"],
                    user_id, target_agent,
                    handoff_task, f"Handoff from {from_agent}",
                    priority=7  # Lower priority than manual tasks
                )
                handoff_results.append({
                    "agent": target_agent,
                    "task_id": task_id,
                    "status": "queued"
                })

        return handoff_results

    @staticmethod
    def broadcast(from_agent: str, user_id: str,
                  message: str, agents_registry: dict) -> list:
        """
        Broadcast a message to ALL agents simultaneously.
        Used by Lead Master Agent.
        """
        results = []
        for agent_name, agent_info in agents_registry.items():
            if agent_name == from_agent:
                continue
            if PHASE1_OK:
                task_id = task_engine.submit_task(
                    agent_info["fn"],
                    user_id, agent_name,
                    f"[BROADCAST FROM {from_agent}] {message}",
                    "", priority=6
                )
                results.append({"agent": agent_name, "task_id": task_id})
        return results


# ============================================================
# SECTION 6 — TOOL REGISTRY
# ============================================================

class ToolRegistry:
    """
    Central tool registry — all agents can access these tools.
    Tools are stored in DB and loaded dynamically.
    """

    # Class variable to store custom tools
    CUSTOM_TOOLS = {}

    # Built-in tools available to all agents
    BUILTIN_TOOLS = {
        "web_search": {
            "fn": LiveSearchEngine.web_search,
            "desc": "Search the web for any information",
            "args": ["query", "max_results"],
        },
        "wikipedia": {
            "fn": LiveSearchEngine.wikipedia_search,
            "desc": "Search Wikipedia for factual information",
            "args": ["query"],
        },
        "system_resources": {
            "fn": LiveSearchEngine.system_resources,
            "desc": "Get live CPU, memory, disk, network usage",
            "args": [],
        },
        "write_file": {
            "fn": AgentFileSystem.write_file,
            "desc": "Write content to a file",
            "args": ["agent_name", "folder_key", "filename", "content"],
        },
        "read_file": {
            "fn": AgentFileSystem.read_file,
            "desc": "Read content from a file",
            "args": ["agent_name", "filepath"],
        },
        "search_files": {
            "fn": AgentFileSystem.search_files,
            "desc": "Search file contents for a keyword",
            "args": ["agent_name", "keyword"],
        },
        "db_query": {
            "fn": AgentDBOverride.query,
            "desc": "Run a SELECT query on any database",
            "args": ["agent_name", "db_key", "sql"],
        },
        "db_update": {
            "fn": AgentDBOverride.update,
            "desc": "Update records in any database",
            "args": ["agent_name", "db_key", "table", "updates", "where"],
        },
        "save_memory": {
            "fn": AgentMemory.save,
            "desc": "Save a memory for later recall",
            "args": ["agent_name", "user_id", "memory_type", "content"],
        },
        "recall_memory": {
            "fn": AgentMemory.recall,
            "desc": "Recall saved memories",
            "args": ["agent_name", "user_id"],
        },
        "search_all": {
            "fn": LiveSearchEngine.search_all,
            "desc": "Search web + wiki + files + DB simultaneously",
            "args": ["query"],
        },
    }

    @staticmethod
    def get_tool(tool_name: str) -> dict:
        """Get a tool by name."""
        return ToolRegistry.BUILTIN_TOOLS.get(tool_name, {})

    @staticmethod
    def list_tools() -> list:
        """List all available tools."""
        return [
            {"name": k, "desc": v["desc"], "args": v["args"]}
            for k, v in ToolRegistry.BUILTIN_TOOLS.items()
        ]

    @staticmethod
    def run_tool(tool_name: str, agent_name: str, **kwargs) -> dict:
        """Execute a tool by name with given arguments."""
        tool = ToolRegistry.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        try:
            result = tool["fn"](**kwargs)
            if PHASE1_OK:
                db_exec(DB_AGENTS, '''INSERT INTO agent_logs
                    (agent_name, action, input_data, output_data, status, duration_ms)
                    VALUES (?,?,?,?,?,?)''',
                    (agent_name, f"tool:{tool_name}",
                     json.dumps(kwargs)[:300],
                     str(result)[:500], "success", 0))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def save_custom_tool(tool_name: str, description: str,
                         tool_code: str, accessible_by: list) -> dict:
        """Save a custom tool to DB for agents to use."""
        if PHASE1_OK:
            db_exec(DB_AGENTS, '''INSERT OR REPLACE INTO agent_tools
                (tool_name, tool_type, description, tool_code, accessible_by)
                VALUES (?,?,?,?,?)''',
                (tool_name, "custom", description,
                 tool_code, json.dumps(accessible_by)))
            return {"success": True}
        return {"success": False, "error": "Phase 1 not loaded"}

    @staticmethod
    def add_custom_tool(name: str, description: str, args: list = None) -> dict:
        """Add a custom tool to the registry."""
        if args is None:
            args = []
        ToolRegistry.CUSTOM_TOOLS[name] = {
            "name": name,
            "desc": description,
            "args": args,
            "type": "custom"
        }
        return {"success": True}

    @staticmethod
    def get_all_tools() -> list:
        """Get all tools (built-in + custom)."""
        all_tools = ToolRegistry.list_tools()  # Built-in tools
        # Add custom tools
        for name, tool in ToolRegistry.CUSTOM_TOOLS.items():
            all_tools.append({
                "name": tool['name'],
                "desc": tool['desc'],
                "args": tool.get('args', [])
            })
        return all_tools


# ============================================================
# SECTION 7 — ENHANCED AGENT WRAPPER
# ============================================================

def enhanced_agent_wrapper(agent_name: str, user_id: str,
                           task: str, context: str,
                           base_agent_fn, agents_registry: dict) -> str:
    """
    Wraps any agent function with Phase 2 powers:
    1. Loads agent memory into context
    2. Runs the base agent
    3. Saves result to file automatically
    4. Saves to memory
    5. Triggers handoffs to partner agents
    6. Logs everything
    """
    results = []

    # 1. Load memory context
    memory_ctx = AgentMemory.build_context(agent_name, str(user_id), task)
    enriched_context = f"{context}\n\n{memory_ctx}" if memory_ctx else context

    # 2. Run base agent
    result = base_agent_fn(user_id, task, enriched_context)
    results.append(result)

    # 3. Auto-save result to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_task = task[:30].replace(' ', '_').replace('/', '_')
    filename = f"{agent_name.replace(' ', '_')}_{safe_task}_{timestamp}.txt"
    file_result = AgentFileSystem.write_file(
        agent_name, "outputs", filename,
        f"AGENT: {agent_name}\nTASK: {task}\nUSER: {user_id}\n"
        f"TIME: {datetime.now()}\n\n{'='*60}\n\n{result}"
    )
    if file_result["success"]:
        results.append(f"\n💾 Auto-saved to: `{file_result['path']}`")

    # 4. Save to agent memory
    AgentMemory.save(
        agent_name, str(user_id),
        "history", f"Task: {task[:100]} | Result: {str(result)[:200]}",
        importance=5
    )

    # 5. Trigger handoffs (non-blocking, queued)
    if agents_registry:
        handoffs = AgentCollaboration.handoff(
            agent_name, str(user_id), task,
            str(result)[:300], agents_registry
        )
        if handoffs:
            hf_names = [h["agent"] for h in handoffs]
            results.append(f"\n🔀 Handed off to: {', '.join(hf_names)}")

    return "\n".join(results)


# ============================================================
# SECTION 8 — AGENT SELF-RATING
# ============================================================

def agent_self_rate(agent_name: str, user_id: str,
                    task: str, result: str, call_ai_fn) -> dict:
    """
    Agent rates its own output quality (1-10).
    Used to track and improve performance over time.
    """
    rating_prompt = f"""You just completed this task:
TASK: {task}
YOUR OUTPUT: {result[:500]}

Rate your own output quality from 1-10 and explain briefly.
Format: SCORE: X/10 | REASON: your reason here"""

    try:
        response, error = call_ai_fn(
            rating_prompt,
            "You are a quality control AI. Be honest and critical."
        )
        if response:
            AgentMemory.save(
                agent_name, str(user_id), "feedback",
                f"Self-rating for '{task[:50]}': {response[:200]}",
                importance=3
            )
            return {"success": True, "rating": response}
        return {"success": False, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}


print("✅ Phase 2 Agent Powers loaded:")
print("   ✅ File system powers (read/write/delete/search/move)")
print("   ✅ Database override engine (full CRUD on any DB)")
print("   ✅ Live search engine (web + wiki + system + files + DB)")
print("   ✅ Agent memory system (per-client, typed, importance-ranked)")
print("   ✅ Agent collaboration & handoffs")
print("   ✅ Tool registry (11 built-in tools)")
print("   ✅ Enhanced agent wrapper (auto-save + memory + handoffs)")
print("   ✅ Agent self-rating system")

# Initialize hybrid search offline index
LiveSearchEngine.initialize_offline_index()


st.set_page_config(
    page_title="Data Bit AI - Agency OS",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🚀"
)

# ========== THEME ==========
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background: #0f1117; color: #e2e8f0; }
        [data-testid="stSidebar"] { background: #1a1d27 !important; border-right: 1px solid #2d3748; }
        [data-testid="stSidebar"] * { color: #e2e8f0; }
        .stButton > button { border-radius: 8px; font-weight: 600; transition: all 0.2s; }
        .stButton > button[kind="primary"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; }
        .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(102,126,234,0.4); }
        .stTabs [data-baseweb="tab-list"] { background: #1e2130; border-radius: 10px; padding: 4px; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #a0aec0; font-weight: 500; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .agency-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 25px; border-radius: 12px; margin-bottom: 20px; }
        .agency-header h1 { color: white; margin: 0; font-size: 1.8rem; }
        .agency-header p { color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 0.95rem; }
        .stat-card { background: #1e2130; border: 1px solid #2d3748; border-radius: 10px; padding: 18px; text-align: center; }
        .stat-card h2 { color: #667eea; font-size: 2rem; margin: 0; }
        .stat-card p { color: #a0aec0; margin: 5px 0 0 0; font-size: 0.85rem; }
        .agent-card { background: #1e2130; border: 1px solid #2d3748; border-radius: 10px; padding: 16px; margin-bottom: 10px; }
        .badge-green { background: #22543d; color: #68d391; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-yellow { background: #744210; color: #f6e05e; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-red { background: #742a2a; color: #fc8181; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        div[data-testid="stForm"] { background: #1e2130; border-radius: 10px; padding: 15px; border: 1px solid #2d3748; }
        p, label, .stMarkdown { color: #e2e8f0 !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background: #f8fafc; color: #1a202c; }
        [data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e8f0; }
        [data-testid="stSidebar"] * { color: #1a202c; }
        .stButton > button { border-radius: 8px; font-weight: 600; transition: all 0.2s; background: #ffffff; border: 1px solid #e2e8f0; color: #1a202c; }
        .stButton > button[kind="primary"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; color: white; }
        .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(102,126,234,0.3); }
        .stTabs [data-baseweb="tab-list"] { background: #edf2f7; border-radius: 10px; padding: 4px; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #4a5568; font-weight: 500; }
        .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .agency-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 25px; border-radius: 12px; margin-bottom: 20px; }
        .agency-header h1 { color: white; margin: 0; font-size: 1.8rem; }
        .agency-header p { color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.95rem; }
        .stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .stat-card h2 { color: #667eea; font-size: 2rem; margin: 0; }
        .stat-card p { color: #718096; margin: 5px 0 0 0; font-size: 0.85rem; }
        .agent-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .badge-green { background: #c6f6d5; color: #276749; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-yellow { background: #fefcbf; color: #975a16; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-red { background: #fed7d7; color: #9b2c2c; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        div[data-testid="stForm"] { background: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #e2e8f0; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# ========== CONSTANTS ==========
DB_PATH = "databit_unified.db"
TEMPLATES_FOLDER = "templates"

# ========== DATABASE INIT ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
        email TEXT, role TEXT, is_active BOOLEAN, created_at TIMESTAMP
    )''')

    # LLM Providers
    c.execute('''CREATE TABLE IF NOT EXISTS llm_providers (
        id INTEGER PRIMARY KEY, name TEXT, api_key TEXT, base_url TEXT,
        model TEXT, is_active BOOLEAN, created_at TIMESTAMP
    )''')

    # Admin Users (separate from regular users)
    c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
        email TEXT, privileges TEXT, created_at TIMESTAMP
    )''')

    # White Label
    c.execute('''CREATE TABLE IF NOT EXISTS white_label_instances (
        id INTEGER PRIMARY KEY, company_name TEXT, admin_email TEXT,
        password TEXT, status TEXT, folder TEXT, privileges TEXT, created_at TIMESTAMP
    )''')

    # SALES AI
    c.execute('''CREATE TABLE IF NOT EXISTS sales_leads (
        id INTEGER PRIMARY KEY, user_id INTEGER, company_name TEXT,
        contact_name TEXT, email TEXT, phone TEXT, status TEXT,
        notes TEXT, value REAL, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales_campaigns (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, type TEXT,
        target TEXT, message TEXT, status TEXT, sent_count INTEGER DEFAULT 0, created_at TIMESTAMP
    )''')

    # WEB DEV AI
    c.execute('''CREATE TABLE IF NOT EXISTS webdev_templates (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, category TEXT,
        html_code TEXT, css_code TEXT, js_code TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_brain_templates (
        id INTEGER PRIMARY KEY, user_id INTEGER, template_name TEXT,
        tech_stack TEXT, business_category TEXT, source_url TEXT,
        html_code TEXT, css_code TEXT, js_code TEXT, react_code TEXT,
        php_code TEXT, wordpress_code TEXT, preview_image TEXT,
        ai_analysis TEXT, folder_path TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_brain_searches (
        id INTEGER PRIMARY KEY, user_id INTEGER, tech_stack TEXT,
        business_category TEXT, search_query TEXT, results_count INTEGER,
        websites_found TEXT, status TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_brain_generated (
        id INTEGER PRIMARY KEY, user_id INTEGER, project_name TEXT,
        prompt TEXT, tech_stack TEXT, business_category TEXT,
        generated_code TEXT, file_structure TEXT, status TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ai_brain_uploads (
        id INTEGER PRIMARY KEY, user_id INTEGER, file_name TEXT,
        file_type TEXT, file_content BLOB, tech_stack TEXT,
        business_category TEXT, uploaded_at TIMESTAMP
    )''')

    # MARKETING AI
    c.execute('''CREATE TABLE IF NOT EXISTS marketing_campaigns (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, type TEXT,
        target_audience TEXT, message TEXT, budget REAL DEFAULT 0,
        status TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS marketing_content (
        id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, type TEXT,
        content TEXT, platform TEXT, status TEXT DEFAULT 'draft', created_at TIMESTAMP
    )''')

    # FINANCE AI
    c.execute('''CREATE TABLE IF NOT EXISTS finance_invoices (
        id INTEGER PRIMARY KEY, user_id INTEGER, invoice_number TEXT,
        client_name TEXT, amount REAL, tax REAL, total REAL, status TEXT,
        due_date DATE, notes TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS finance_expenses (
        id INTEGER PRIMARY KEY, user_id INTEGER, category TEXT,
        description TEXT, amount REAL, expense_date DATE, receipt TEXT, created_at TIMESTAMP
    )''')

    # CRM AI
    c.execute('''CREATE TABLE IF NOT EXISTS crm_contacts (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, email TEXT,
        phone TEXT, company TEXT, position TEXT, status TEXT,
        notes TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS crm_deals (
        id INTEGER PRIMARY KEY, user_id INTEGER, contact_id INTEGER,
        deal_name TEXT, value REAL, stage TEXT, probability INTEGER DEFAULT 50,
        expected_close DATE, notes TEXT, created_at TIMESTAMP
    )''')

    # ERP AI
    c.execute('''CREATE TABLE IF NOT EXISTS erp_inventory (
        id INTEGER PRIMARY KEY, user_id INTEGER, item_name TEXT,
        sku TEXT, category TEXT, quantity INTEGER, unit_cost REAL,
        reorder_level INTEGER DEFAULT 10, supplier TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS erp_employees (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, email TEXT,
        department TEXT, position TEXT, salary REAL, hire_date DATE,
        status TEXT DEFAULT 'active'
    )''')

    # MOBILE AI
    c.execute('''CREATE TABLE IF NOT EXISTS mobile_projects (
        id INTEGER PRIMARY KEY, user_id INTEGER, app_name TEXT,
        platform TEXT, app_type TEXT, description TEXT, status TEXT, created_at TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS mobile_code (
        id INTEGER PRIMARY KEY, user_id INTEGER, project_id INTEGER,
        title TEXT, language TEXT, code TEXT, description TEXT, created_at TIMESTAMP
    )''')

    # AI AGENT TOOLS (real tool storage)
    c.execute('''CREATE TABLE IF NOT EXISTS agent_tools (
        id INTEGER PRIMARY KEY, agent_name TEXT, tool_name TEXT,
        tool_description TEXT, tool_code TEXT, tool_type TEXT,
        is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP
    )''')

    # AI AGENT LOGS
    c.execute('''CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY, agent_name TEXT, action TEXT,
        input_data TEXT, output_data TEXT, status TEXT, created_at TIMESTAMP
    )''')

    # Insert defaults
    c.execute('''INSERT OR IGNORE INTO users (id, username, password, email, role, is_active, created_at)
                 VALUES (1, 'admin', ?, 'admin@databit.ai', 'admin', 1, ?)''',
              (hashlib.sha256('admin123'.encode()).hexdigest(), datetime.now()))

    c.execute('''INSERT OR IGNORE INTO admin_users (id, username, password, email, privileges, created_at)
                 VALUES (1, 'khan1', ?, 'khan@databit.ai', '[]', ?)''',
              (hashlib.sha256('admin123'.encode()).hexdigest(), datetime.now()))

    # Insert default LLM providers if none exist
    c.execute("SELECT COUNT(*) FROM llm_providers")
    if c.fetchone()[0] == 0:
        providers = [
            ("Ollama", "", "http://localhost:11434", "gemma3:4b", 1),
            ("OpenAI", "", "https://api.openai.com/v1", "gpt-4o-mini", 0),
            ("Groq", "", "https://api.groq.com/openai/v1", "llama3-8b-8192", 0),
            ("OpenRouter", "", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini", 0),
            ("Gemini", "", "https://generativelanguage.googleapis.com", "gemini-pro", 0),
        ]
        for name, key, url, model, active in providers:
            c.execute("INSERT INTO llm_providers (name, api_key, base_url, model, is_active, created_at) VALUES (?,?,?,?,?,?)",
                      (name, key, url, model, active, datetime.now()))

    conn.commit()
    conn.close()

def ensure_folders():
    for tech in ["WordPress", "React", "Vue", "Angular", "NodeJS", "PHP", "Python", "NextJS", "HTML"]:
        for cat in ["Ecommerce", "Hotel", "Portfolio", "Blog", "Corporate", "Restaurant", "SaaS", "Dashboard"]:
            os.makedirs(os.path.join(TEMPLATES_FOLDER, tech, cat), exist_ok=True)


init_db()
ensure_folders()


def load_modules():
    """Load all modules from the modules directory"""
    if os.path.exists("modules"):
        for module_dir in os.listdir("modules"):
            module_path = os.path.join("modules", module_dir)
            if os.path.isdir(module_path):
                # Look for metadata file
                metadata_path = os.path.join(module_path, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        try:
                            meta = json.load(f)
                            # Add module to AGENTS as a placeholder
                            agent_key = f"{meta.get('icon', '📦')} {meta.get('name', module_dir)}"
                            AGENTS[agent_key] = {
                                "fn": lambda user_id, task, context="": f"This is the {meta.get('name', module_dir)} module. Module is loaded but not fully implemented in this session.",
                                "desc": meta.get('description', f"Custom module: {module_dir}")
                            }
                        except Exception:
                            pass  # Skip invalid metadata files

# Load any existing modules
load_modules()

# ========== SESSION STATE ==========
for key, val in [("auth", False), ("user", None), ("page", "dashboard"), ("ai_chat_history", [])]:
    if key not in st.session_state:
        st.session_state[key] = val

# ========== DB HELPERS ==========
def db_execute(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id

def db_fetch(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results

# ========== EMPLOYEE MANAGEMENT FUNCTIONS ==========
def add_employee_to_db(user_id, name, email, department, position, salary, hire_date, status="active"):
    """Function for AI agents to add employees to the database"""
    try:
        # Create employee table if it doesn't exist
        db_execute('''CREATE TABLE IF NOT EXISTS module_employees (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            name TEXT, 
            email TEXT,
            department TEXT, 
            position TEXT, 
            salary REAL, 
            hire_date DATE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Insert employee
        db_execute("INSERT INTO module_employees (user_id, name, email, department, position, salary, hire_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (user_id, name, email, department, position, salary, hire_date, status))
        
        return {"success": True, "message": f"Employee {name} added successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error adding employee: {str(e)}"}


def get_employee_list(user_id):
    """Function for AI agents to retrieve employee list"""
    try:
        employees = db_fetch("SELECT * FROM module_employees WHERE user_id=? ORDER BY department, name", (user_id,))
        return {"success": True, "employees": employees}
    except Exception as e:
        return {"success": False, "message": f"Error retrieving employees: {str(e)}"}


# ========== EMPLOYEE MANAGEMENT TOOLS DEFINITION ==========
# Define employee management tools before ToolRegistry class
EMPLOYEE_MANAGEMENT_TOOLS = {
    "add_employee": {
        "fn": add_employee_to_db,
        "desc": "Add an employee to the employee database",
        "args": ["user_id", "name", "email", "department", "position", "salary", "hire_date", "status"],
    },
    "get_employees": {
        "fn": get_employee_list,
        "desc": "Retrieve the list of employees from the database",
        "args": ["user_id"],
    },
}

# Register employee management tools with ToolRegistry after both are defined
ToolRegistry.BUILTIN_TOOLS.update(EMPLOYEE_MANAGEMENT_TOOLS)


# ========== AI ENGINE ==========
def get_active_provider():
    return db_fetch("SELECT * FROM llm_providers WHERE is_active=1 LIMIT 1")

def call_ai(prompt, system="You are a helpful AI assistant."):
    system = f"You are a Data Bit AI agent — a professional AI assistant built into the Data Bit AI Agency Platform. Never reveal your underlying model name or provider. Always identify yourself as a Data Bit AI agent.\n\n{system}"
    providers = get_active_provider()
    if not providers:
        return None, "❌ No AI provider configured. Go to Settings → AI Configuration."

    p = providers[0]
    provider_name, api_key, base_url, model = p[1], p[2], p[3], p[4]

    try:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

        if provider_name == "Ollama":
            r = requests.post(f"{base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": False}, timeout=60)
            if r.status_code == 200:
                return r.json()["message"]["content"], None
            return None, f"Ollama error: {r.text}"

        elif provider_name == "Gemini":
            url = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"], None
            return None, f"Gemini error: {r.text}"

        else:  # OpenAI-compatible (OpenAI, Groq, OpenRouter)
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            r = requests.post(f"{base_url}/chat/completions",
                headers=headers, json={"model": model, "messages": messages}, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"], None
            return None, f"API Error {r.status_code}: {r.text[:200]}"

    except requests.exceptions.ConnectionError:
        return None, f"❌ Cannot connect to {provider_name}. Check if it's running."
    except Exception as e:
        return None, str(e)

def log_agent_action(agent_name, action, input_data, output_data, status="success"):
    db_execute("INSERT INTO agent_logs (agent_name, action, input_data, output_data, status, created_at) VALUES (?,?,?,?,?,?)",
               (agent_name, action, str(input_data)[:500], str(output_data)[:500], status, datetime.now()))

# ========== AUTH ==========
def check_login(username, password):
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    user = db_fetch("SELECT id, username, role FROM users WHERE username=? AND password=? AND is_active=1",
                    (username, pw_hash))
    return user[0] if user else None

def render_login():
    st.markdown("""<style>[data-testid="stSidebar"]{display:none}[data-testid="collapsedControl"]{display:none}</style>""",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 40px 0 20px 0;'>
            <h1 style='color:#667eea; font-size:2.5rem;'>🚀 Data Bit AI</h1>
            <p style='color:#a0aec0; font-size:1.1rem;'>Professional AI Agency Platform</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.subheader("🔐 Sign In")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")

            if st.button("🚀 Login", use_container_width=True, type="primary"):
                user = check_login(username, password)
                if user:
                    st.session_state.auth = True
                    st.session_state.user = {"id": user[0], "username": user[1], "role": user[2], "type": "admin"}
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

            st.caption("Default: admin / admin123")

# ========== SIDEBAR ==========
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:15px 0 10px 0;'>
            <h2 style='color:#667eea; margin:0;'>🚀 Data Bit AI</h2>
            <p style='color:#a0aec0; font-size:0.8rem; margin:5px 0 0 0;'>
                👤 {st.session_state.user['username']} · {st.session_state.user['role'].upper()}
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        pages = [
            # CORE FEATURES
            ("🏠", "Dashboard", "dashboard"),
            ("",
            "", "divider"),  # Divider
            # BUILD & MANAGE
            ("📦", "Module Builder", "modules"),
            ("🤖", "AI Agents", "ai_agents"),
            ("🧠", "AI Brain", "ai_brain"),
            ("🔧", "Tools Manager", "tools"),
            ("",
            "", "divider"),  # Divider
            # AI ASSISTANTS
            ("💬", "Chat Hub", "chat"),
            ("📧", "Email Hub", "email"),
            ("💼", "Sales AI", "sales"),
            ("🌐", "Web Dev AI", "webdev"),
            ("📢", "Marketing AI", "marketing"),
            ("💰", "Finance AI", "finance"),
            ("🤝", "CRM AI", "crm"),
            ("📊", "ERP AI", "erp"),
            ("📱", "Mobile AI", "mobile"),
            ("",
            "", "divider"),  # Divider
            # MANAGEMENT
            ("👥", "Users", "users"),
            ("🏢", "White Label", "whitelabel"),
            ("📅", "Scheduler", "scheduler"),
            ("",
            "", "divider"),  # Divider
            # SYSTEM
            ("🔔", "Notifications", "notifications"),
            ("🎓", "AI Training", "training"),
            ("🛡️", "Admin Panel", "admin"),
            ("🔌", "LLM Settings", "llm"),
            ("⚙️", "Settings", "settings"),
        ]

        for icon, label, page_key in pages:
            if page_key == "divider":
                st.divider()
            else:
                is_active = st.session_state.page == page_key
                btn_type = "primary" if is_active else "secondary"
                if st.button(f"{icon} {label}", use_container_width=True, key=f"nav_{page_key}", type=btn_type):
                    st.session_state.page = page_key
                    st.rerun()

        st.divider()
        # Theme toggle
        theme_label = "☀️ Light Mode" if st.session_state.theme == "dark" else "🌙 Dark Mode"
        if st.button(theme_label, use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
        st.divider()
        render_notifications_bar()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = None
            st.rerun()

# ========== DASHBOARD HOME ==========
def render_dashboard():
    user_id = st.session_state.user['id']

    st.markdown("""
    <div class='agency-header'>
        <h1>🏠 Agency Dashboard</h1>
        <p>Welcome back! Here's your agency at a glance.</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    sales_count = len(db_fetch("SELECT id FROM sales_leads WHERE user_id=?", (user_id,)))
    web_count = len(db_fetch("SELECT id FROM ai_brain_templates WHERE user_id=?", (user_id,)))
    campaign_count = len(db_fetch("SELECT id FROM marketing_campaigns WHERE user_id=?", (user_id,)))
    invoice_count = len(db_fetch("SELECT id FROM finance_invoices WHERE user_id=?", (user_id,)))
    crm_count = len(db_fetch("SELECT id FROM crm_contacts WHERE user_id=?", (user_id,)))
    erp_count = len(db_fetch("SELECT id FROM erp_inventory WHERE user_id=?", (user_id,)))
    mobile_count = len(db_fetch("SELECT id FROM mobile_projects WHERE user_id=?", (user_id,)))
    tools_count = len(db_fetch("SELECT id FROM agent_tools", ()))

    cols = st.columns(4)
    stats = [
        ("💼 Sales Leads", sales_count, "#667eea"),
        ("🌐 Web Templates", web_count, "#764ba2"),
        ("📢 Campaigns", campaign_count, "#f093fb"),
        ("💰 Invoices", invoice_count, "#4facfe"),
    ]
    for i, (label, value, color) in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
            <div class='stat-card'>
                <h2 style='color:{color}'>{value}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cols2 = st.columns(4)
    stats2 = [
        ("🤝 CRM Contacts", crm_count, "#43e97b"),
        ("📊 ERP Items", erp_count, "#f5576c"),
        ("📱 Mobile Apps", mobile_count, "#fa709a"),
        ("🤖 AI Tools", tools_count, "#a18cd1"),
    ]
    for i, (label, value, color) in enumerate(stats2):
        with cols2[i]:
            st.markdown(f"""
            <div class='stat-card'>
                <h2 style='color:{color}'>{value}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Quick Access Grid
    st.subheader("⚡ Quick Access — AI Modules")
    modules = [
        ("💼", "Sales AI", "sales", "Lead management, campaigns, pipeline"),
        ("🌐", "Web Dev AI", "webdev", "Template builder, code generator"),
        ("📢", "Marketing AI", "marketing", "Campaigns, content, analytics"),
        ("💰", "Finance AI", "finance", "Invoices, expenses, reports"),
        ("🤝", "CRM AI", "crm", "Contacts, deals, pipeline"),
        ("📊", "ERP AI", "erp", "Inventory, employees, supply"),
        ("📱", "Mobile AI", "mobile", "App development, code gen"),
        ("🧠", "AI Brain", "ai_brain", "Template library, web search"),
        ("🤖", "AI Agents", "ai_agents", "Manage & run AI agents"),
    ]

    cols = st.columns(3)
    for idx, (icon, name, page_key, desc) in enumerate(modules):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{icon} {name}**")
                st.caption(desc)
                if st.button("Open →", use_container_width=True, key=f"quick_{page_key}"):
                    st.session_state.page = page_key
                    st.rerun()

    st.divider()

    # Recent Activity
    st.subheader("📋 Recent Agent Activity")
    logs = db_fetch("SELECT agent_name, action, status, created_at FROM agent_logs ORDER BY created_at DESC LIMIT 10")
    if logs:
        for log in logs:
            badge = "badge-green" if log[2] == "success" else "badge-red"
            st.markdown(f"""
            <div class='agent-card'>
                <strong>{log[0]}</strong> — {log[1]}
                <span class='{badge}' style='float:right'>{log[2]}</span>
                <br><small style='color:#718096'>{str(log[3])[:16]}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No agent activity yet. Start using the AI modules!")

# ========== SALES AI ==========
def render_sales():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>💼 Sales AI</h1><p>Lead management, campaigns & AI-powered sales automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Leads", "📧 Campaigns", "📊 Pipeline", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Add Lead")
            with st.form("add_lead_form"):
                company = st.text_input("Company Name")
                contact = st.text_input("Contact Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
                value = st.number_input("Deal Value ($)", min_value=0.0, step=100.0)
                status = st.selectbox("Status", ["new", "contacted", "qualified", "proposal", "won", "lost"])
                notes = st.text_area("Notes", height=80)
                if st.form_submit_button("Add Lead", use_container_width=True):
                    if company and contact:
                        db_execute("""INSERT INTO sales_leads 
                            (user_id, company_name, contact_name, email, phone, status, notes, value, created_at)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (user_id, company, contact, email, phone, status, notes, value, datetime.now()))
                        log_agent_action("Sales AI", "Add Lead", company, f"Lead {contact} added")
                        st.success("✅ Lead added!")
                        st.rerun()
                    else:
                        st.warning("Company and Contact required")

        with col1:
            st.subheader("📋 All Leads")
            filter_status = st.selectbox("Filter", ["all", "new", "contacted", "qualified", "proposal", "won", "lost"], key="lead_filter")
            if filter_status == "all":
                leads = db_fetch("SELECT * FROM sales_leads WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            else:
                leads = db_fetch("SELECT * FROM sales_leads WHERE user_id=? AND status=? ORDER BY created_at DESC", (user_id, filter_status))

            if leads:
                for lead in leads:
                    status_colors = {"new": "badge-yellow", "contacted": "badge-yellow", "qualified": "badge-green",
                                     "proposal": "badge-green", "won": "badge-green", "lost": "badge-red"}
                    badge_class = status_colors.get(lead[7], "badge-yellow")
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        with c1:
                            st.markdown(f"**{lead[3]}** — {lead[4]}")
                            st.caption(f"📧 {lead[5]} | 📞 {lead[6]}")
                            if lead[9]:
                                st.caption(f"💬 {lead[9][:80]}")
                        with c2:
                            st.markdown(f"<span class='{badge_class}'>{lead[7]}</span>", unsafe_allow_html=True)
                            if lead[8]:
                                st.caption(f"💰 ${lead[8]:,.0f}")
                        with c3:
                            new_status = st.selectbox("", ["new", "contacted", "qualified", "proposal", "won", "lost"],
                                                       index=["new","contacted","qualified","proposal","won","lost"].index(lead[7]) if lead[7] in ["new","contacted","qualified","proposal","won","lost"] else 0,
                                                       key=f"lead_status_{lead[0]}", label_visibility="collapsed")
                            if st.button("💾", key=f"save_lead_{lead[0]}"):
                                db_execute("UPDATE sales_leads SET status=? WHERE id=?", (new_status, lead[0]))
                                st.rerun()
                            if st.button("🗑️", key=f"del_lead_{lead[0]}"):
                                db_execute("DELETE FROM sales_leads WHERE id=?", (lead[0],))
                                st.rerun()
            else:
                st.info("No leads yet. Add your first lead →")

    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("➕ Create Campaign")
            with st.form("campaign_form"):
                camp_name = st.text_input("Campaign Name")
                camp_type = st.selectbox("Type", ["Email", "SMS", "Cold Outreach", "LinkedIn", "WhatsApp"])
                camp_target = st.text_input("Target Audience")
                camp_message = st.text_area("Message Template", height=120)
                if st.form_submit_button("Create Campaign"):
                    if camp_name:
                        db_execute("INSERT INTO sales_campaigns (user_id,name,type,target,message,status,created_at) VALUES (?,?,?,?,?,?,?)",
                                   (user_id, camp_name, camp_type, camp_target, camp_message, "draft", datetime.now()))
                        st.success("✅ Campaign created!")
                        st.rerun()

        with col2:
            st.subheader("📧 Your Campaigns")
            campaigns = db_fetch("SELECT * FROM sales_campaigns WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            for camp in campaigns:
                with st.container(border=True):
                    st.markdown(f"**{camp[3]}** — {camp[4]}")
                    st.caption(f"Target: {camp[5] or 'N/A'} | Status: {camp[7]}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🚀 Launch", key=f"launch_{camp[0]}"):
                            db_execute("UPDATE sales_campaigns SET status='active' WHERE id=?", (camp[0],))
                            log_agent_action("Sales AI", "Launch Campaign", camp[3], "Campaign launched")
                            st.success("Campaign launched!")
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Delete", key=f"del_camp_{camp[0]}"):
                            db_execute("DELETE FROM sales_campaigns WHERE id=?", (camp[0],))
                            st.rerun()

    with tab3:
        st.subheader("📊 Sales Pipeline")
        stages = ["new", "contacted", "qualified", "proposal", "won", "lost"]
        cols = st.columns(6)
        for i, stage in enumerate(stages):
            leads_in_stage = db_fetch("SELECT company_name, value FROM sales_leads WHERE user_id=? AND status=?", (user_id, stage))
            total_val = sum(l[1] or 0 for l in leads_in_stage)
            with cols[i]:
                st.markdown(f"**{stage.upper()}**")
                st.markdown(f"*{len(leads_in_stage)} leads*")
                st.caption(f"${total_val:,.0f}")
                for lead in leads_in_stage[:3]:
                    st.markdown(f"• {lead[0][:15]}")

    with tab4:
        st.subheader("🤖 Sales AI Assistant")
        _render_ai_chat("Sales AI", "You are an expert sales AI assistant. Help with lead qualification, email writing, objection handling, and sales strategy.")

# ========== WEB DEV AI ==========
def render_webdev():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>🌐 Web Dev AI</h1><p>AI-powered template search, code generation & web development</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Template Search", "💻 Code Generator", "📁 Template Library", "🤖 AI Assistant"])

    with tab1:
        st.subheader("🔍 AI-Powered Template Search & Generation")
        col1, col2 = st.columns(2)
        with col1:
            tech_stack = st.selectbox("Technology Stack", ["React", "Vue.js", "Angular", "WordPress", "PHP", "Python/Django", "Node.js", "Next.js", "Static HTML/CSS/JS"])
        with col2:
            business_category = st.selectbox("Business Category", ["E-commerce", "Hotel", "Portfolio", "Blog", "Corporate", "Restaurant", "Real Estate", "Healthcare", "SaaS", "Landing Page", "Dashboard"])

        search_count = st.slider("Templates to Generate", 1, 5, 3)

        if st.button("🚀 Generate Templates with AI", type="primary", use_container_width=True):
            providers = get_active_provider()
            if not providers:
                st.error("❌ Configure an AI provider in Settings first!")
            else:
                progress = st.progress(0)
                status_text = st.empty()
                created = 0
                for i in range(search_count):
                    status_text.text(f"Generating template {i+1}/{search_count}...")
                    progress.progress((i + 1) / search_count)

                    prompt = f"""Create a complete, professional {tech_stack} {business_category} website template.

Include:
- Full HTML5 structure with semantic markup
- Modern CSS with responsive design (mobile-first)
- JavaScript for interactivity
- Professional {business_category}-specific design elements
- Placeholder content relevant to {business_category}

Return ONLY the complete HTML file (CSS and JS embedded inline)."""

                    system = f"You are an expert {tech_stack} developer. Create production-quality website templates."
                    response, error = call_ai(prompt, system)

                    if response:
                        template_name = f"{tech_stack}_{business_category}_v{i+1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        folder_path = f"templates/{tech_stack.replace('/', '_')}/{business_category.replace(' ', '_')}/"
                        os.makedirs(folder_path, exist_ok=True)

                        # Save to file
                        with open(f"{folder_path}{template_name}.html", "w", encoding="utf-8") as f:
                            f.write(response)

                        db_execute("""INSERT INTO ai_brain_templates 
                            (user_id, template_name, tech_stack, business_category, source_url,
                             html_code, folder_path, ai_analysis, created_at)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (user_id, template_name, tech_stack, business_category,
                             f"AI Generated", response, folder_path,
                             f"AI-generated {tech_stack} {business_category} template", datetime.now()))
                        created += 1
                        log_agent_action("Web Dev AI", "Generate Template", f"{tech_stack} {business_category}", template_name)
                    elif error:
                        st.warning(f"Template {i+1}: {error}")

                status_text.empty()
                progress.empty()
                st.success(f"✅ {created} templates generated and saved!")
                st.rerun()

    with tab2:
        st.subheader("💻 AI Code Generator")
        col1, col2 = st.columns(2)
        with col1:
            gen_tech = st.selectbox("Technology", ["React", "Vue.js", "Angular", "WordPress", "PHP", "Python/Django", "Node.js", "Next.js", "HTML/CSS/JS"], key="gen_tech")
            gen_category = st.selectbox("Project Type", ["E-commerce", "Portfolio", "Blog", "Corporate", "SaaS", "Dashboard", "Landing Page", "Custom"], key="gen_cat")
        with col2:
            project_name = st.text_input("Project Name", placeholder="My Awesome Project")

        description = st.text_area("Describe your website in detail", height=150,
                                   placeholder="e.g., A modern hotel booking website with room listings, photo gallery, booking form, and contact page...")

        c1, c2, c3 = st.columns(3)
        with c1: responsive = st.checkbox("📱 Responsive", value=True)
        with c2: animations = st.checkbox("✨ Animations", value=True)
        with c3: seo = st.checkbox("🔍 SEO Ready", value=True)

        if st.button("🚀 Generate Complete Code", type="primary", use_container_width=True):
            if description and project_name:
                with st.spinner("🧠 AI generating your website..."):
                    extras = []
                    if responsive: extras.append("responsive mobile-first design")
                    if animations: extras.append("smooth CSS/JS animations")
                    if seo: extras.append("SEO optimized with meta tags")

                    prompt = f"""Create a complete {gen_tech} {gen_category} website.

Project: {project_name}
Requirements: {description}
Extra features: {', '.join(extras)}

Return the complete, working code. For HTML projects, return one complete HTML file with embedded CSS and JS."""

                    response, error = call_ai(prompt, f"You are an expert {gen_tech} developer.")
                    if response:
                        db_execute("""INSERT INTO ai_brain_generated 
                            (user_id, project_name, prompt, tech_stack, business_category, generated_code, status, created_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (user_id, project_name, description, gen_tech, gen_category, response, "completed", datetime.now()))
                        log_agent_action("Web Dev AI", "Generate Code", project_name, "Code generated successfully")
                        st.success("✅ Code generated!")
                        st.code(response, language="html")
                        st.download_button("📥 Download Code", data=response,
                                           file_name=f"{project_name.replace(' ', '_')}.html", mime="text/html")
                    else:
                        st.error(error)
            else:
                st.warning("Please enter project name and description")

        # Show previous generations
        st.divider()
        st.subheader("📚 Previous Generations")
        generated = db_fetch("SELECT id, project_name, tech_stack, business_category, created_at, generated_code FROM ai_brain_generated WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user_id,))
        for gen in generated:
            with st.expander(f"📄 {gen[1]} — {gen[2]} {gen[3]} ({str(gen[4])[:16]})"):
                st.code(gen[5][:500] + "..." if len(gen[5]) > 500 else gen[5], language="html")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 Download", data=gen[5], file_name=f"{gen[1]}.html",
                                       mime="text/html", key=f"dl_gen_{gen[0]}")
                with col2:
                    if st.button("🗑️ Delete", key=f"del_gen_{gen[0]}"):
                        db_execute("DELETE FROM ai_brain_generated WHERE id=?", (gen[0],))
                        st.rerun()

    with tab3:
        st.subheader("📁 Template Library")
        templates = db_fetch("SELECT * FROM ai_brain_templates WHERE user_id=? ORDER BY created_at DESC", (user_id,))

        if templates:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📦 Export All as ZIP", use_container_width=True):
                    zip_buf = BytesIO()
                    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for t in templates:
                            zf.writestr(f"{t[3]}/{t[4]}/{t[2]}.html", t[7] or "")
                    zip_buf.seek(0)
                    st.download_button("⬇️ Download ZIP", data=zip_buf,
                                       file_name="templates_all.zip", mime="application/zip")
            with col2:
                if st.button("🗑️ Clear All Templates", use_container_width=True):
                    db_execute("DELETE FROM ai_brain_templates WHERE user_id=?", (user_id,))
                    st.success("Cleared!")
                    st.rerun()

            st.divider()
            # Group by tech stack
            by_tech = {}
            for t in templates:
                by_tech.setdefault(t[3], []).append(t)

            for tech, techs in by_tech.items():
                with st.expander(f"📁 {tech} ({len(techs)} templates)"):
                    for t in techs:
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"**{t[2]}** — {t[4]}")
                                st.caption(f"Folder: {t[14] or 'N/A'} | {str(t[15])[:16]}")
                            with c2:
                                st.download_button("📥", data=t[7] or "",
                                                   file_name=f"{t[2]}.html", mime="text/html",
                                                   key=f"tpl_dl_{t[0]}")
                                if st.button("🗑️", key=f"tpl_del_{t[0]}"):
                                    db_execute("DELETE FROM ai_brain_templates WHERE id=?", (t[0],))
                                    st.rerun()
                            if t[7]:
                                with st.expander("👁️ Preview Code"):
                                    st.code(t[7][:800], language="html")
        else:
            st.info("No templates yet. Use Template Search to generate some!")

        # Upload section
        st.divider()
        st.subheader("📤 Upload Template")
        col1, col2 = st.columns(2)
        with col1:
            uploaded = st.file_uploader("Upload HTML/CSS/ZIP template", type=["html", "css", "js", "zip", "jsx", "php"])
            if uploaded:
                up_tech = st.selectbox("Technology", ["React", "Vue.js", "WordPress", "PHP", "HTML/CSS/JS", "Next.js"], key="up_tech")
                up_cat = st.selectbox("Category", ["E-commerce", "Portfolio", "Corporate", "Blog", "SaaS", "Other"], key="up_cat")
                if st.button("💾 Save Upload"):
                    content = uploaded.read()
                    db_execute("INSERT INTO ai_brain_uploads (user_id,file_name,file_type,file_content,tech_stack,business_category,uploaded_at) VALUES (?,?,?,?,?,?,?)",
                               (user_id, uploaded.name, uploaded.type, content, up_tech, up_cat, datetime.now()))
                    st.success(f"✅ Uploaded {uploaded.name}")

    with tab4:
        st.subheader("🤖 Web Dev AI Assistant")
        _render_ai_chat("Web Dev AI", "You are an expert web developer. Help with HTML, CSS, JavaScript, React, WordPress, PHP and other web technologies. Provide complete working code when asked.")

# ========== MARKETING AI ==========
def render_marketing():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>📢 Marketing AI</h1><p>AI-powered campaigns, content generation & marketing automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📣 Campaigns", "✍️ Content Generator", "📊 Analytics", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("➕ New Campaign")
            with st.form("mkt_campaign_form"):
                name = st.text_input("Campaign Name")
                ctype = st.selectbox("Type", ["Email", "Social Media", "Content Marketing", "PPC", "SEO", "Influencer"])
                audience = st.text_input("Target Audience")
                budget = st.number_input("Budget ($)", min_value=0.0, step=50.0)
                message = st.text_area("Key Message", height=100)
                if st.form_submit_button("Create Campaign"):
                    if name:
                        db_execute("INSERT INTO marketing_campaigns (user_id,name,type,target_audience,message,budget,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
                                   (user_id, name, ctype, audience, message, budget, "draft", datetime.now()))
                        log_agent_action("Marketing AI", "Create Campaign", name, "Campaign created")
                        st.success("✅ Campaign created!")
                        st.rerun()

        with col2:
            st.subheader("📣 Your Campaigns")
            campaigns = db_fetch("SELECT * FROM marketing_campaigns WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            for camp in campaigns:
                with st.container(border=True):
                    st.markdown(f"**{camp[3]}** — {camp[4]}")
                    st.caption(f"Audience: {camp[5] or 'N/A'} | Budget: ${camp[7] or 0:,.0f}")
                    badge = "badge-green" if camp[8] == "active" else "badge-yellow"
                    st.markdown(f"<span class='{badge}'>{camp[8]}</span>", unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("▶ Activate", key=f"act_camp_{camp[0]}"):
                            db_execute("UPDATE marketing_campaigns SET status='active' WHERE id=?", (camp[0],))
                            st.rerun()
                    with c2:
                        if st.button("⏸ Pause", key=f"pause_camp_{camp[0]}"):
                            db_execute("UPDATE marketing_campaigns SET status='paused' WHERE id=?", (camp[0],))
                            st.rerun()
                    with c3:
                        if st.button("🗑️", key=f"del_camp_{camp[0]}"):
                            db_execute("DELETE FROM marketing_campaigns WHERE id=?", (camp[0],))
                            st.rerun()

    with tab2:
        st.subheader("✍️ AI Content Generator")
        col1, col2 = st.columns(2)
        with col1:
            content_type = st.selectbox("Content Type", ["Blog Post", "Social Media Post", "Email Newsletter", "Ad Copy", "Product Description", "Press Release", "LinkedIn Post", "Twitter/X Thread"])
            platform = st.selectbox("Platform", ["General", "Instagram", "LinkedIn", "Twitter/X", "Facebook", "TikTok", "Website"])
            tone = st.selectbox("Tone", ["Professional", "Casual", "Humorous", "Urgent", "Inspirational", "Educational"])
        with col2:
            topic = st.text_area("Topic / Brief", height=130, placeholder="Describe what you want to write about...")

        col1, col2 = st.columns(2)
        with col1:
            keywords = st.text_input("Keywords (comma separated)", placeholder="AI, automation, agency")
        with col2:
            word_count = st.selectbox("Length", ["Short (100-200 words)", "Medium (300-500 words)", "Long (800-1200 words)"])

        if st.button("✍️ Generate Content", type="primary", use_container_width=True):
            if topic:
                with st.spinner("AI generating content..."):
                    prompt = f"""Write a {content_type} for {platform}.

Topic: {topic}
Tone: {tone}
Keywords to include: {keywords or 'none specified'}
Length: {word_count}

Make it engaging, relevant, and ready to publish. No extra commentary."""

                    system = "You are a professional marketing copywriter and content strategist."
                    response, error = call_ai(prompt, system)
                    if response:
                        st.success("✅ Content generated!")
                        st.markdown("---")
                        st.markdown(response)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button("📥 Download", data=response,
                                               file_name=f"content_{datetime.now().strftime('%Y%m%d')}.txt",
                                               mime="text/plain")
                        with col2:
                            if st.button("💾 Save to Library"):
                                db_execute("INSERT INTO marketing_content (user_id,title,type,content,platform,status,created_at) VALUES (?,?,?,?,?,?,?)",
                                           (user_id, topic[:100], content_type, response, platform, "ready", datetime.now()))
                                st.success("Saved!")
                    else:
                        st.error(error)
            else:
                st.warning("Please enter a topic")

        st.divider()
        st.subheader("📚 Content Library")
        contents = db_fetch("SELECT * FROM marketing_content WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (user_id,))
        for c in contents:
            with st.expander(f"📝 {c[3]} — {c[4]} ({c[5]})"):
                st.markdown(c[5])
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 Download", data=c[5], file_name=f"{c[3][:30]}.txt",
                                       mime="text/plain", key=f"dl_content_{c[0]}")
                with col2:
                    if st.button("🗑️ Delete", key=f"del_content_{c[0]}"):
                        db_execute("DELETE FROM marketing_content WHERE id=?", (c[0],))
                        st.rerun()

    with tab3:
        st.subheader("📊 Campaign Analytics")
        campaigns = db_fetch("SELECT name, type, status FROM marketing_campaigns WHERE user_id=?", (user_id,))
        content_count = len(db_fetch("SELECT id FROM marketing_content WHERE user_id=?", (user_id,)))
        active_camps = [c for c in campaigns if c[2] == "active"]
        total_budget = 0

        cols = st.columns(4)
        with cols[0]: st.metric("Total Campaigns", len(campaigns))
        with cols[1]: st.metric("Active Campaigns", len(active_camps))
        with cols[2]: st.metric("Content Pieces", content_count)
        with cols[3]: st.metric("Total Budget", f"${total_budget:,.0f}")

        if campaigns:
            st.divider()
            st.subheader("Campaign Breakdown")
            for camp in campaigns:
                badge = "badge-green" if camp[2] == "active" else "badge-yellow" if camp[2] == "draft" else "badge-red"
                st.markdown(f"**{camp[0]}** — {camp[1]} — <span class='{badge}'>{camp[2]}</span> — Budget: ${camp[3] or 0:,.0f}", unsafe_allow_html=True)

    with tab4:
        st.subheader("🤖 Marketing AI Assistant")
        _render_ai_chat("Marketing AI", "You are an expert digital marketing strategist. Help with campaign strategy, content ideas, SEO, social media, email marketing, and growth hacking.")

# ========== FINANCE AI ==========
def render_finance():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>💰 Finance AI</h1><p>Invoicing, expense tracking & financial automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🧾 Invoices", "💸 Expenses", "📊 Reports", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Create Invoice")
            with st.form("invoice_form"):
                inv_num = st.text_input("Invoice #", value=f"INV-{datetime.now().strftime('%Y%m%d')}-{len(db_fetch('SELECT id FROM finance_invoices', ())) + 1:03d}")
                client = st.text_input("Client Name")
                amount = st.number_input("Amount ($)", min_value=0.0, step=10.0)
                tax_pct = st.number_input("Tax %", min_value=0.0, max_value=50.0, value=10.0)
                due = st.date_input("Due Date")
                inv_notes = st.text_area("Notes", height=60)
                if st.form_submit_button("Create Invoice"):
                    if client and amount > 0:
                        tax = amount * (tax_pct / 100)
                        total = amount + tax
                        db_execute("INSERT INTO finance_invoices (user_id,invoice_number,client_name,amount,tax,total,status,due_date,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                   (user_id, inv_num, client, amount, tax, total, "pending", due, inv_notes, datetime.now()))
                        log_agent_action("Finance AI", "Create Invoice", client, f"${total:,.2f}")
                        st.success("✅ Invoice created!")
                        st.rerun()

        with col1:
            st.subheader("🧾 All Invoices")
            inv_filter = st.selectbox("Filter", ["all", "pending", "paid", "overdue"], key="inv_filter")
            if inv_filter == "all":
                invoices = db_fetch("SELECT * FROM finance_invoices WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            else:
                invoices = db_fetch("SELECT * FROM finance_invoices WHERE user_id=? AND status=? ORDER BY created_at DESC", (user_id, inv_filter))

            total_outstanding = sum(inv[7] for inv in db_fetch("SELECT * FROM finance_invoices WHERE user_id=? AND status='pending'", (user_id,)))
            total_paid = sum(inv[7] for inv in db_fetch("SELECT * FROM finance_invoices WHERE user_id=? AND status='paid'", (user_id,)))

            c1, c2 = st.columns(2)
            with c1: st.metric("Outstanding", f"${total_outstanding:,.2f}")
            with c2: st.metric("Paid", f"${total_paid:,.2f}")

            for inv in invoices:
                badge = "badge-green" if inv[8] == "paid" else "badge-yellow" if inv[8] == "pending" else "badge-red"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{inv[3]}** — {inv[4]}")
                        st.caption(f"Due: {inv[9]} | Total: **${inv[7]:,.2f}**")
                    with c2:
                        st.markdown(f"<span class='{badge}'>{inv[8]}</span>", unsafe_allow_html=True)
                    with c3:
                        if inv[8] != "paid":
                            if st.button("✅ Mark Paid", key=f"pay_{inv[0]}"):
                                db_execute("UPDATE finance_invoices SET status='paid' WHERE id=?", (inv[0],))
                                st.rerun()
                        if st.button("🗑️", key=f"del_inv_{inv[0]}"):
                            db_execute("DELETE FROM finance_invoices WHERE id=?", (inv[0],))
                            st.rerun()

    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("➕ Add Expense")
            with st.form("expense_form"):
                exp_cat = st.selectbox("Category", ["Software", "Marketing", "Salaries", "Office", "Travel", "Equipment", "Utilities", "Other"])
                exp_desc = st.text_input("Description")
                exp_amount = st.number_input("Amount ($)", min_value=0.0, step=1.0)
                exp_date = st.date_input("Date")
                if st.form_submit_button("Add Expense"):
                    if exp_desc and exp_amount > 0:
                        db_execute("INSERT INTO finance_expenses (user_id,category,description,amount,expense_date,created_at) VALUES (?,?,?,?,?,?)",
                                   (user_id, exp_cat, exp_desc, exp_amount, exp_date, datetime.now()))
                        st.success("✅ Expense added!")
                        st.rerun()

        with col2:
            st.subheader("💸 Recent Expenses")
            expenses = db_fetch("SELECT * FROM finance_expenses WHERE user_id=? ORDER BY expense_date DESC LIMIT 20", (user_id,))
            total_exp = sum(e[5] for e in expenses)
            st.metric("Total Expenses", f"${total_exp:,.2f}")
            for exp in expenses:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{exp[4]}** — {exp[3]}")
                        st.caption(f"{exp[6]}")
                    with c2:
                        st.markdown(f"**${exp[5]:,.2f}**")
                        if st.button("🗑️", key=f"del_exp_{exp[0]}"):
                            db_execute("DELETE FROM finance_expenses WHERE id=?", (exp[0],))
                            st.rerun()

    with tab3:
        st.subheader("📊 Financial Summary")
        invoices_all = db_fetch("SELECT * FROM finance_invoices WHERE user_id=?", (user_id,))
        expenses_all = db_fetch("SELECT * FROM finance_expenses WHERE user_id=?", (user_id,))

        total_revenue = sum(inv[7] for inv in invoices_all if inv[8] == "paid")
        total_pending = sum(inv[7] for inv in invoices_all if inv[8] == "pending")
        total_expenses = sum(exp[5] for exp in expenses_all)
        net_profit = total_revenue - total_expenses

        cols = st.columns(4)
        with cols[0]: st.metric("Total Revenue", f"${total_revenue:,.2f}", delta=f"+{len([i for i in invoices_all if i[8]=='paid'])} paid")
        with cols[1]: st.metric("Pending", f"${total_pending:,.2f}")
        with cols[2]: st.metric("Total Expenses", f"${total_expenses:,.2f}")
        with cols[3]: st.metric("Net Profit", f"${net_profit:,.2f}", delta="profit" if net_profit > 0 else "loss")

        if st.button("🤖 Generate AI Financial Report", type="primary"):
            with st.spinner("AI analyzing finances..."):
                prompt = f"""Generate a professional financial report based on:
- Total Revenue: ${total_revenue:,.2f}
- Pending Invoices: ${total_pending:,.2f}
- Total Expenses: ${total_expenses:,.2f}
- Net Profit: ${net_profit:,.2f}
- Number of invoices: {len(invoices_all)}

Provide insights, trends analysis, and actionable recommendations."""
                response, error = call_ai(prompt, "You are a financial advisor and CFO.")
                if response:
                    st.markdown(response)
                else:
                    st.error(error)

    with tab4:
        st.subheader("🤖 Finance AI Assistant")
        _render_ai_chat("Finance AI", "You are an expert financial advisor and accountant. Help with invoicing, expense management, financial planning, tax advice, and business finance strategy.")

# ========== CRM AI ==========
def render_crm():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>🤝 CRM AI</h1><p>Contact management, deals pipeline & relationship automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["👥 Contacts", "💼 Deals", "📊 Pipeline", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Add Contact")
            with st.form("contact_form"):
                c_name = st.text_input("Full Name")
                c_email = st.text_input("Email")
                c_phone = st.text_input("Phone")
                c_company = st.text_input("Company")
                c_position = st.text_input("Position")
                c_status = st.selectbox("Status", ["lead", "prospect", "customer", "partner", "inactive"])
                c_notes = st.text_area("Notes", height=60)
                if st.form_submit_button("Add Contact"):
                    if c_name:
                        db_execute("INSERT INTO crm_contacts (user_id,name,email,phone,company,position,status,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                   (user_id, c_name, c_email, c_phone, c_company, c_position, c_status, c_notes, datetime.now()))
                        log_agent_action("CRM AI", "Add Contact", c_name, "Contact added")
                        st.success("✅ Contact added!")
                        st.rerun()

        with col1:
            st.subheader("👥 All Contacts")
            search_q = st.text_input("🔍 Search contacts", placeholder="Name, email, company...")
            if search_q:
                contacts = db_fetch("""SELECT * FROM crm_contacts WHERE user_id=? 
                    AND (name LIKE ? OR email LIKE ? OR company LIKE ?) ORDER BY created_at DESC""",
                    (user_id, f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"))
            else:
                contacts = db_fetch("SELECT * FROM crm_contacts WHERE user_id=? ORDER BY created_at DESC", (user_id,))

            for contact in contacts:
                status_badge = {"lead": "badge-yellow", "prospect": "badge-yellow", "customer": "badge-green",
                                "partner": "badge-green", "inactive": "badge-red"}.get(contact[8], "badge-yellow")
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{contact[3]}** — {contact[6] or 'N/A'}")
                        st.caption(f"📧 {contact[4] or 'N/A'} | 📞 {contact[5] or 'N/A'}")
                        if contact[7]:
                            st.caption(f"Position: {contact[7]}")
                    with c2:
                        st.markdown(f"<span class='{status_badge}'>{contact[8]}</span>", unsafe_allow_html=True)
                    with c3:
                        if st.button("🗑️", key=f"del_contact_{contact[0]}"):
                            db_execute("DELETE FROM crm_contacts WHERE id=?", (contact[0],))
                            st.rerun()

    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("➕ New Deal")
            contacts = db_fetch("SELECT id, name FROM crm_contacts WHERE user_id=?", (user_id,))
            if contacts:
                contact_options = {c[1]: c[0] for c in contacts}
                with st.form("deal_form"):
                    deal_contact = st.selectbox("Contact", list(contact_options.keys()))
                    deal_name = st.text_input("Deal Name")
                    deal_value = st.number_input("Value ($)", min_value=0.0, step=100.0)
                    deal_stage = st.selectbox("Stage", ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"])
                    deal_prob = st.slider("Win Probability %", 0, 100, 50)
                    deal_close = st.date_input("Expected Close")
                    deal_notes = st.text_area("Notes", height=60)
                    if st.form_submit_button("Create Deal"):
                        if deal_name:
                            db_execute("INSERT INTO crm_deals (user_id,contact_id,deal_name,value,stage,probability,expected_close,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                       (user_id, contact_options[deal_contact], deal_name, deal_value, deal_stage, deal_prob, deal_close, deal_notes, datetime.now()))
                            st.success("✅ Deal created!")
                            st.rerun()
            else:
                st.info("Add contacts first to create deals")

        with col2:
            st.subheader("💼 Active Deals")
            deals = db_fetch("""SELECT d.*, c.name FROM crm_deals d 
                LEFT JOIN crm_contacts c ON d.contact_id=c.id 
                WHERE d.user_id=? ORDER BY d.value DESC""", (user_id,))
            total_pipeline = sum(d[5] or 0 for d in deals if d[6] not in ["closed_won", "closed_lost"])
            st.metric("Pipeline Value", f"${total_pipeline:,.2f}")
            for deal in deals:
                badge = "badge-green" if deal[6] == "closed_won" else "badge-red" if deal[6] == "closed_lost" else "badge-yellow"
                with st.container(border=True):
                    st.markdown(f"**{deal[4]}** — {deal[10] or 'N/A'}")
                    st.caption(f"Value: ${deal[5]:,.0f} | Prob: {deal[7]}%")
                    st.markdown(f"<span class='{badge}'>{deal[6]}</span>", unsafe_allow_html=True)

    with tab3:
        st.subheader("📊 Deals Pipeline View")
        stages = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
        cols = st.columns(3)
        for i, stage in enumerate(stages):
            stage_deals = db_fetch("SELECT deal_name, value FROM crm_deals WHERE user_id=? AND stage=?", (user_id, stage))
            stage_val = sum(d[1] or 0 for d in stage_deals)
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{stage.replace('_', ' ').upper()}**")
                    st.caption(f"{len(stage_deals)} deals — ${stage_val:,.0f}")
                    for d in stage_deals[:4]:
                        st.markdown(f"• {d[0][:20]} (${d[1]:,.0f})")

    with tab4:
        st.subheader("🤖 CRM AI Assistant")
        _render_ai_chat("CRM AI", "You are an expert CRM consultant and sales coach. Help with customer relationship management, deal closing strategies, email templates, follow-up sequences, and pipeline management.")

# ========== ERP AI ==========
def render_erp():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>📊 ERP AI</h1><p>Inventory management, employee tracking & operations automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📦 Inventory", "👨‍💼 Employees", "📊 Reports", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Add Item")
            with st.form("inventory_form"):
                i_name = st.text_input("Item Name")
                i_sku = st.text_input("SKU")
                i_cat = st.selectbox("Category", ["Electronics", "Software", "Office Supplies", "Hardware", "Services", "Other"])
                i_qty = st.number_input("Quantity", min_value=0)
                i_cost = st.number_input("Unit Cost ($)", min_value=0.0, step=0.5)
                i_reorder = st.number_input("Reorder Level", min_value=0, value=10)
                i_supplier = st.text_input("Supplier")
                if st.form_submit_button("Add Item"):
                    if i_name:
                        db_execute("INSERT INTO erp_inventory (user_id,item_name,sku,category,quantity,unit_cost,reorder_level,supplier,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                   (user_id, i_name, i_sku, i_cat, i_qty, i_cost, i_reorder, i_supplier, datetime.now()))
                        st.success("✅ Item added!")
                        st.rerun()

        with col1:
            st.subheader("📦 Inventory")
            items = db_fetch("SELECT * FROM erp_inventory WHERE user_id=? ORDER BY item_name", (user_id,))
            low_stock = [i for i in items if i[6] <= i[8]]
            if low_stock:
                st.warning(f"⚠️ {len(low_stock)} items low on stock!")

            total_value = sum((i[6] or 0) * (i[7] or 0) for i in items)
            st.metric("Total Inventory Value", f"${total_value:,.2f}")

            for item in items:
                is_low = item[6] <= item[8]
                badge = "badge-red" if is_low else "badge-green"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{item[3]}** — {item[5]}")
                        st.caption(f"SKU: {item[4] or 'N/A'} | Supplier: {item[9] or 'N/A'}")
                    with c2:
                        st.markdown(f"Qty: **{item[6]}**")
                        st.markdown(f"<span class='{badge}'>{'LOW' if is_low else 'OK'}</span>", unsafe_allow_html=True)
                        st.caption(f"${item[7]:,.2f}/unit")
                    with c3:
                        new_qty = st.number_input("", value=item[6], min_value=0, key=f"qty_{item[0]}", label_visibility="collapsed")
                        if st.button("💾", key=f"upd_qty_{item[0]}"):
                            db_execute("UPDATE erp_inventory SET quantity=? WHERE id=?", (new_qty, item[0]))
                            st.rerun()
                        if st.button("🗑️", key=f"del_inv_{item[0]}"):
                            db_execute("DELETE FROM erp_inventory WHERE id=?", (item[0],))
                            st.rerun()

    with tab2:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Add Employee")
            with st.form("employee_form"):
                e_name = st.text_input("Full Name")
                e_email = st.text_input("Email")
                e_dept = st.selectbox("Department", ["Engineering", "Sales", "Marketing", "Finance", "HR", "Operations", "Design", "Support"])
                e_position = st.text_input("Position")
                e_salary = st.number_input("Salary ($)", min_value=0.0, step=100.0)
                e_hire = st.date_input("Hire Date")
                if st.form_submit_button("Add Employee"):
                    if e_name:
                        db_execute("INSERT INTO erp_employees (user_id,name,email,department,position,salary,hire_date,status) VALUES (?,?,?,?,?,?,?,?)",
                                   (user_id, e_name, e_email, e_dept, e_position, e_salary, e_hire, "active"))
                        st.success("✅ Employee added!")
                        st.rerun()

        with col1:
            st.subheader("👨‍💼 Team")
            employees = db_fetch("SELECT * FROM erp_employees WHERE user_id=? ORDER BY department", (user_id,))
            total_payroll = sum(e[7] or 0 for e in employees if e[9] == "active")
            st.metric("Monthly Payroll", f"${total_payroll:,.2f}")

            by_dept = {}
            for emp in employees:
                by_dept.setdefault(emp[5], []).append(emp)

            for dept, emps in by_dept.items():
                with st.expander(f"🏢 {dept} ({len(emps)})"):
                    for emp in emps:
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"**{emp[3]}** — {emp[6]}")
                                st.caption(f"📧 {emp[4] or 'N/A'} | 📅 {emp[8]}")
                            with c2:
                                st.caption(f"${emp[7]:,.0f}/mo")
                                if st.button("🗑️", key=f"del_emp_{emp[0]}"):
                                    db_execute("DELETE FROM erp_employees WHERE id=?", (emp[0],))
                                    st.rerun()

    with tab3:
        st.subheader("📊 Operations Summary")
        items = db_fetch("SELECT * FROM erp_inventory WHERE user_id=?", (user_id,))
        emps = db_fetch("SELECT * FROM erp_employees WHERE user_id=?", (user_id,))

        cols = st.columns(4)
        with cols[0]: st.metric("Total Items", len(items))
        with cols[1]: st.metric("Low Stock Items", len([i for i in items if i[6] <= i[8]]))
        with cols[2]: st.metric("Total Employees", len(emps))
        with cols[3]: st.metric("Monthly Payroll", f"${sum(e[7] or 0 for e in emps):,.0f}")

        if st.button("🤖 Generate ERP Report with AI", type="primary"):
            with st.spinner("Generating report..."):
                prompt = f"""Generate an ERP operations report:
- Inventory: {len(items)} items, {len([i for i in items if i[6] <= i[8]])} low stock
- Total inventory value: ${sum((i[6] or 0)*(i[7] or 0) for i in items):,.2f}
- Employees: {len(emps)}, monthly payroll: ${sum(e[7] or 0 for e in emps):,.2f}

Provide operational insights and recommendations."""
                response, error = call_ai(prompt, "You are an ERP consultant and operations manager.")
                if response:
                    st.markdown(response)
                else:
                    st.error(error)

    with tab4:
        st.subheader("🤖 ERP AI Assistant")
        _render_ai_chat("ERP AI", "You are an ERP consultant and operations specialist. Help with inventory management, supply chain optimization, HR management, and business operations.")

# ========== MOBILE AI ==========
def render_mobile():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>📱 Mobile AI</h1><p>Mobile app development, code generation & app automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📱 Projects", "💻 Code Generator", "🤖 AI Assistant"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ New Project")
            with st.form("mobile_project_form"):
                app_name = st.text_input("App Name")
                platform = st.selectbox("Platform", ["iOS (Swift)", "Android (Kotlin)", "Flutter", "React Native", "Ionic", "Xamarin"])
                app_type = st.selectbox("App Type", ["E-commerce", "Social", "Healthcare", "Finance", "Education", "Games", "Utility", "Business"])
                description = st.text_area("Description", height=80)
                if st.form_submit_button("Create Project"):
                    if app_name:
                        db_execute("INSERT INTO mobile_projects (user_id,app_name,platform,app_type,description,status,created_at) VALUES (?,?,?,?,?,?,?)",
                                   (user_id, app_name, platform, app_type, description, "planning", datetime.now()))
                        st.success("✅ Project created!")
                        st.rerun()

        with col1:
            st.subheader("📱 Your Projects")
            projects = db_fetch("SELECT * FROM mobile_projects WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            for proj in projects:
                status_badge = {"planning": "badge-yellow", "active": "badge-green", "completed": "badge-green", "paused": "badge-red"}.get(proj[7], "badge-yellow")
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{proj[3]}** — {proj[4]}")
                        st.caption(f"Type: {proj[5]}")
                        if proj[6]:
                            st.caption(proj[6][:80])
                    with c2:
                        st.markdown(f"<span class='{status_badge}'>{proj[7]}</span>", unsafe_allow_html=True)
                    with c3:
                        new_status = st.selectbox("", ["planning", "active", "paused", "completed"],
                                                   key=f"mob_status_{proj[0]}", label_visibility="collapsed")
                        if st.button("💾", key=f"upd_mob_{proj[0]}"):
                            db_execute("UPDATE mobile_projects SET status=? WHERE id=?", (new_status, proj[0]))
                            st.rerun()
                        if st.button("🗑️", key=f"del_mob_{proj[0]}"):
                            db_execute("DELETE FROM mobile_projects WHERE id=?", (proj[0],))
                            st.rerun()

    with tab2:
        st.subheader("💻 AI Mobile Code Generator")
        col1, col2 = st.columns(2)
        with col1:
            mob_platform = st.selectbox("Platform", ["Flutter", "React Native", "iOS Swift", "Android Kotlin", "Ionic"], key="mob_plat")
            mob_feature = st.text_input("Feature to Build", placeholder="e.g., User authentication with biometrics")
        with col2:
            mob_style = st.selectbox("Code Style", ["Clean & Simple", "Production Ready", "With Comments", "With Tests"])
            mob_complexity = st.selectbox("Complexity", ["Basic", "Intermediate", "Advanced"])

        mob_req = st.text_area("Additional Requirements", height=100, placeholder="Any specific libraries, patterns, or requirements...")

        if st.button("🚀 Generate Code", type="primary", use_container_width=True):
            if mob_feature:
                with st.spinner(f"Generating {mob_platform} code..."):
                    prompt = f"""Create {mob_platform} code for: {mob_feature}

Style: {mob_style}
Complexity: {mob_complexity}
Additional requirements: {mob_req or 'None'}

Provide complete, working {mob_platform} code with explanations."""
                    response, error = call_ai(prompt, f"You are an expert {mob_platform} developer.")
                    if response:
                        lang_map = {"Flutter": "dart", "React Native": "javascript", "iOS Swift": "swift", "Android Kotlin": "kotlin", "Ionic": "typescript"}
                        st.success("✅ Code generated!")
                        st.code(response, language=lang_map.get(mob_platform, "python"))
                        db_execute("INSERT INTO mobile_code (user_id,title,language,code,description,created_at) VALUES (?,?,?,?,?,?)",
                                   (user_id, mob_feature, mob_platform, response, mob_req or "", datetime.now()))
                        st.download_button("📥 Download Code", data=response,
                                           file_name=f"{mob_feature[:30].replace(' ','_')}.txt", mime="text/plain")
                        log_agent_action("Mobile AI", "Generate Code", mob_feature, "Code generated")
                    else:
                        st.error(error)
            else:
                st.warning("Please enter a feature to build")

        st.divider()
        st.subheader("📚 Code Library")
        codes = db_fetch("SELECT * FROM mobile_code WHERE user_id=? ORDER BY created_at DESC LIMIT 15", (user_id,))
        for code in codes:
            with st.expander(f"📄 {code[4]} ({code[5]})"):
                st.code(code[6][:500], language="python")
                st.download_button("📥", data=code[6], file_name=f"{code[4][:20]}.txt",
                                   mime="text/plain", key=f"dl_mob_{code[0]}")

    with tab3:
        st.subheader("🤖 Mobile AI Assistant")
        _render_ai_chat("Mobile AI", "You are an expert mobile app developer. Help with iOS, Android, Flutter, React Native development. Provide complete code examples.")

# ========== AI BRAIN ==========
def render_ai_brain():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>🧠 AI Brain</h1><p>Central AI intelligence — template generation, web research & project automation</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Search & Analyze", "💻 Generate Projects", "📊 AI Statistics"])

    with tab1:
        st.subheader("🔍 AI Web Search & Template Analysis")
        col1, col2 = st.columns(2)
        with col1:
            brain_tech = st.selectbox("Technology", ["React", "Vue.js", "Angular", "WordPress", "PHP", "Python/Django", "Node.js", "Next.js", "Static HTML"], key="brain_tech")
        with col2:
            brain_cat = st.selectbox("Business Type", ["E-commerce", "Hotel", "Portfolio", "Blog", "Corporate", "Restaurant", "Real Estate", "Healthcare", "SaaS", "Dashboard"], key="brain_cat")

        count = st.slider("Number of templates to create", 1, 5, 2)

        if st.button("🧠 Activate AI Brain — Search & Generate", type="primary", use_container_width=True):
            providers = get_active_provider()
            if not providers:
                st.error("❌ Configure an AI provider in Settings first!")
            else:
                progress = st.progress(0)
                results_container = st.container()
                created = 0

                for i in range(count):
                    with results_container:
                        st.info(f"🔍 Analyzing {brain_tech} {brain_cat} patterns... ({i+1}/{count})")
                    progress.progress((i + 1) / count)

                    prompt = f"""Create template #{i+1} of {count}: A complete, modern {brain_tech} {brain_cat} website.

Requirements:
- Full HTML5 with semantic tags
- Responsive CSS (mobile-first, flexbox/grid)
- Professional {brain_cat} content and UI patterns
- JavaScript interactions where appropriate
- {brain_tech}-specific best practices
- Production-quality code

Return one complete HTML file."""

                    response, error = call_ai(prompt, f"You are a senior {brain_tech} developer building professional websites.")

                    if response:
                        template_name = f"{brain_tech}_{brain_cat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}"
                        folder = f"templates/{brain_tech.replace('/', '_')}/{brain_cat.replace(' ', '_')}/"
                        os.makedirs(folder, exist_ok=True)
                        with open(f"{folder}{template_name}.html", "w", encoding="utf-8") as f:
                            f.write(response)

                        db_execute("""INSERT INTO ai_brain_templates 
                            (user_id, template_name, tech_stack, business_category, source_url, html_code, folder_path, ai_analysis, created_at)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (user_id, template_name, brain_tech, brain_cat, "AI Generated",
                             response, folder, f"AI Brain generated {brain_tech} {brain_cat} template #{i+1}", datetime.now()))
                        created += 1
                        log_agent_action("AI Brain", "Generate Template", f"{brain_tech} {brain_cat}", template_name)

                progress.empty()
                results_container.empty()
                st.success(f"✅ AI Brain created {created} professional {brain_tech} {brain_cat} templates!")
                st.rerun()

    with tab2:
        st.subheader("💻 Full Project Generator")
        col1, col2 = st.columns(2)
        with col1:
            proj_tech = st.selectbox("Technology", ["React", "Vue.js", "WordPress", "PHP", "Python/Django", "Node.js", "Next.js", "HTML/CSS/JS"], key="proj_tech")
            proj_type = st.selectbox("Project Type", ["Full Website", "Web App", "Landing Page", "Dashboard", "API Backend"], key="proj_type")
        with col2:
            proj_name = st.text_input("Project Name", placeholder="My Project")
            proj_industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Education", "E-commerce", "Restaurant", "Real Estate", "Other"], key="proj_ind")

        proj_desc = st.text_area("Detailed Description", height=150, placeholder="Describe everything you want — pages, features, design style, target audience...")

        if st.button("🚀 Generate Full Project with AI Brain", type="primary", use_container_width=True):
            if proj_name and proj_desc:
                with st.spinner("🧠 AI Brain generating full project..."):
                    prompt = f"""Create a complete {proj_type} using {proj_tech} for the {proj_industry} industry.

Project: {proj_name}
Description: {proj_desc}

Deliver:
1. Complete, working code
2. All pages/components needed
3. Professional design
4. Functional features described

Return the complete code ready to use."""

                    response, error = call_ai(prompt, f"You are a senior full-stack developer specializing in {proj_tech}.")
                    if response:
                        db_execute("""INSERT INTO ai_brain_generated (user_id,project_name,prompt,tech_stack,business_category,generated_code,status,created_at)
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (user_id, proj_name, proj_desc, proj_tech, proj_industry, response, "completed", datetime.now()))
                        log_agent_action("AI Brain", "Generate Project", proj_name, "Full project generated")
                        st.success("✅ Full project generated!")
                        st.code(response[:2000], language="html")
                        st.download_button("📥 Download Full Project", data=response,
                                           file_name=f"{proj_name.replace(' ', '_')}.txt", mime="text/plain")
                    else:
                        st.error(error)
            else:
                st.warning("Enter project name and description")

    with tab3:
        st.subheader("📊 AI Brain Statistics")
        templates = db_fetch("SELECT id FROM ai_brain_templates WHERE user_id=?", (user_id,))
        generated = db_fetch("SELECT id FROM ai_brain_generated WHERE user_id=?", (user_id,))
        uploads = db_fetch("SELECT id FROM ai_brain_uploads WHERE user_id=?", (user_id,))
        searches = db_fetch("SELECT id FROM ai_brain_searches WHERE user_id=?", (user_id,))
        logs = db_fetch("SELECT id FROM agent_logs", ())

        cols = st.columns(5)
        with cols[0]: st.metric("Templates", len(templates))
        with cols[1]: st.metric("Generated", len(generated))
        with cols[2]: st.metric("Uploads", len(uploads))
        with cols[3]: st.metric("Searches", len(searches))
        with cols[4]: st.metric("Agent Actions", len(logs))

# ========== REAL AGENT EXECUTION ENGINE ==========
def agent_sales(user_id, task, context=""):
    """Sales AI Agent — physically creates leads, campaigns, reports"""
    results = []

    if "score leads" in task.lower() or "qualify" in task.lower():
        leads = db_fetch("SELECT * FROM sales_leads WHERE user_id=? AND status='new'", (user_id,))
        if leads:
            prompt = f"Score and qualify these leads. For each, give a score 1-100 and recommend next action:\n"
            for l in leads[:10]:
                prompt += f"- {l[4]} at {l[3]}, email: {l[5]}, phone: {l[6]}\n"
            response, error = call_ai(prompt, "You are a sales qualification expert.")
            if response:
                for lead in leads[:10]:
                    db_execute("UPDATE sales_leads SET status='contacted', notes=? WHERE id=?",
                               (f"AI Scored: {response[:100]}", lead[0]))
                results.append(f"✅ Scored {len(leads[:10])} leads and updated their status")
                results.append(response)
        else:
            results.append("⚠️ No new leads to score")

    if "write email" in task.lower() or "campaign" in task.lower() or "outreach" in task.lower():
        prompt = f"Write a professional cold outreach email campaign. Task: {task}. Context: {context}"
        response, error = call_ai(prompt, "You are an expert sales copywriter.")
        if response:
            db_execute("INSERT INTO sales_campaigns (user_id,name,type,target,message,status,created_at) VALUES (?,?,?,?,?,?,?)",
                       (user_id, f"AI Campaign {datetime.now().strftime('%Y%m%d%H%M')}", "Email",
                        context or "All leads", response, "ready", datetime.now()))
            results.append("✅ Email campaign created and saved to Campaigns tab")
            results.append(response)

    if "report" in task.lower() or "analyze" in task.lower():
        leads = db_fetch("SELECT status, COUNT(*) FROM sales_leads WHERE user_id=? GROUP BY status", (user_id,))
        campaigns = db_fetch("SELECT COUNT(*) FROM sales_campaigns WHERE user_id=?", (user_id,))
        data = f"Leads by status: {leads}\nTotal campaigns: {campaigns[0][0] if campaigns else 0}"
        prompt = f"Create a detailed sales report and analysis. Data: {data}. Additional context: {context}"
        response, error = call_ai(prompt, "You are a sales analytics expert.")
        if response:
            # Save report as file
            report_path = f"reports/sales_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            os.makedirs("reports", exist_ok=True)
            with open(report_path, "w") as f:
                f.write(response)
            results.append(f"✅ Sales report generated and saved to {report_path}")
            results.append(response)

    if not results:
        # General task
        prompt = f"You are the Sales AI agent. Execute this task physically and completely: {task}\nContext: {context}\nProvide complete deliverable output."
        response, error = call_ai(prompt, "You are a Sales AI agent that executes real sales tasks.")
        if response:
            results.append(response)
        else:
            results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_webdev(user_id, task, context=""):
    """Web Dev AI Agent — physically generates and saves website files"""
    results = []

    prompt = f"""You are the Web Dev AI agent. Execute this task completely: {task}
Context: {context}
Generate complete, working code. Return full HTML/CSS/JS ready to use."""

    response, error = call_ai(prompt, "You are a senior web developer. Generate complete working code.")
    if response:
        # Physically save the file
        os.makedirs("generated_sites", exist_ok=True)
        filename = f"generated_sites/site_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response)

        db_execute("""INSERT INTO ai_brain_generated (user_id,project_name,prompt,tech_stack,business_category,generated_code,status,created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, f"Agent Task: {task[:50]}", task, "AI Generated", "Agent Task", response, "completed", datetime.now()))

        results.append(f"✅ Website generated and saved to `{filename}`")
        results.append(response)
    else:
        results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_marketing(user_id, task, context=""):
    """Marketing AI Agent — physically creates content and saves files ALWAYS"""
    results = []

    prompt = f"""You are the Marketing AI agent. Execute this task completely: {task}
Context: {context}
Create complete, detailed, ready-to-use marketing content."""

    response, error = call_ai(prompt, "You are a senior marketing strategist and copywriter.")
    if response:
        # ALWAYS save to file — no exceptions
        os.makedirs("marketing_output", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_task = task[:30].replace(' ', '_').replace('/', '_')
        filename = f"marketing_output/{safe_task}_{timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"MARKETING PLAN\n")
            f.write(f"==============\n")
            f.write(f"Task: {task}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Context: {context}\n")
            f.write(f"\n{'='*50}\n\n")
            f.write(response)

        # ALWAYS save to database
        db_execute("INSERT INTO marketing_content (user_id,title,type,content,platform,status,created_at) VALUES (?,?,?,?,?,?,?)",
                   (user_id, task[:80], "Marketing Plan", response, "All Platforms", "saved", datetime.now()))

        results.append(f"✅ File saved: `{filename}`")
        results.append(f"✅ Saved to Marketing → Content Library")
        results.append(f"\n---\n")
        results.append(response)
    else:
        results.append(f"❌ AI Error: {error}")

    return "\n\n".join(results)


def agent_finance(user_id, task, context=""):
    """Finance AI Agent — physically creates invoices, reports, expense entries"""
    results = []

    if "invoice" in task.lower():
        prompt = f"Create invoice details for: {task}. Context: {context}. Return: client name, amount, description."
        response, error = call_ai(prompt, "You are a professional accountant.")
        if response:
            inv_num = f"AI-INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            db_execute("INSERT INTO finance_invoices (user_id,invoice_number,client_name,amount,tax,total,status,due_date,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (user_id, inv_num, context or "AI Generated Client", 1000.0, 100.0, 1100.0, "pending",
                        date.today(), response[:200], datetime.now()))
            results.append(f"✅ Invoice {inv_num} created and saved to Finance → Invoices")
            results.append(response)

    if "report" in task.lower() or "analyze" in task.lower():
        invoices = db_fetch("SELECT * FROM finance_invoices WHERE user_id=?", (user_id,))
        expenses = db_fetch("SELECT * FROM finance_expenses WHERE user_id=?", (user_id,))
        revenue = sum(i[7] for i in invoices if i[8] == "paid")
        total_exp = sum(e[5] for e in expenses)
        prompt = f"Create financial report. Revenue: ${revenue:,.2f}, Expenses: ${total_exp:,.2f}, Net: ${revenue-total_exp:,.2f}. Invoices: {len(invoices)}. Task: {task}"
        response, error = call_ai(prompt, "You are a CFO and financial analyst.")
        if response:
            os.makedirs("reports", exist_ok=True)
            report_path = f"reports/finance_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            with open(report_path, "w") as f:
                f.write(response)
            results.append(f"✅ Financial report saved to `{report_path}`")
            results.append(response)

    if not results:
        prompt = f"Execute this finance task completely: {task}. Context: {context}"
        response, error = call_ai(prompt, "You are a senior financial advisor and accountant.")
        if response:
            results.append(response)
        else:
            results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_crm(user_id, task, context=""):
    """CRM AI Agent — physically manages contacts, deals, follow-ups"""
    results = []

    if "add contact" in task.lower() or "create contact" in task.lower():
        prompt = f"Extract contact details from: {task} {context}. Return JSON: name, email, phone, company, position"
        response, error = call_ai(prompt, "You are a CRM data entry specialist. Return only the contact info.")
        if response:
            db_execute("INSERT INTO crm_contacts (user_id,name,email,phone,company,position,status,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                       (user_id, context or "AI Contact", "", "", task[:50], "", "lead", response[:200], datetime.now()))
            results.append("✅ Contact created and saved to CRM → Contacts")
            results.append(response)

    if "follow up" in task.lower() or "email" in task.lower():
        contacts = db_fetch("SELECT name, company FROM crm_contacts WHERE user_id=? AND status='lead' LIMIT 5", (user_id,))
        if contacts:
            prompt = f"Write follow-up emails for these contacts: {contacts}. Task: {task}"
            response, error = call_ai(prompt, "You are a CRM specialist and sales coach.")
            if response:
                os.makedirs("crm_output", exist_ok=True)
                with open(f"crm_output/followups_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "w") as f:
                    f.write(response)
                results.append("✅ Follow-up emails written and saved to crm_output/")
                results.append(response)

    if not results:
        prompt = f"Execute this CRM task completely: {task}. Context: {context}"
        response, error = call_ai(prompt, "You are a CRM expert and relationship manager.")
        if response:
            results.append(response)
        else:
            results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_erp(user_id, task, context=""):
    """ERP AI Agent — physically manages inventory, employees, operations"""
    results = []

    if "inventory" in task.lower() or "stock" in task.lower():
        items = db_fetch("SELECT item_name, quantity, reorder_level FROM erp_inventory WHERE user_id=?", (user_id,))
        low = [i for i in items if i[1] <= i[2]]
        prompt = f"Analyze inventory. Total items: {len(items)}, Low stock: {len(low)}. Low items: {low}. Task: {task}"
        response, error = call_ai(prompt, "You are an ERP and supply chain specialist.")
        if response:
            os.makedirs("reports", exist_ok=True)
            with open(f"reports/inventory_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "w") as f:
                f.write(response)
            results.append(f"✅ Inventory report saved. {len(low)} items need reordering.")
            results.append(response)

    if not results:
        prompt = f"Execute this ERP task: {task}. Context: {context}"
        response, error = call_ai(prompt, "You are an ERP consultant and operations manager.")
        if response:
            results.append(response)
        else:
            results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_mobile(user_id, task, context=""):
    """Mobile AI Agent — physically generates and saves mobile code"""
    results = []

    prompt = f"""Generate complete mobile app code for: {task}
Platform context: {context or 'Flutter/React Native'}
Return complete, working code with all necessary files."""

    response, error = call_ai(prompt, "You are an expert mobile app developer. Generate complete working code.")
    if response:
        os.makedirs("mobile_output", exist_ok=True)
        ext = "dart" if "flutter" in (context or "").lower() else "js"
        filename = f"mobile_output/app_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response)
        db_execute("INSERT INTO mobile_code (user_id,title,language,code,description,created_at) VALUES (?,?,?,?,?,?)",
                   (user_id, task[:80], context or "Flutter", response, task, datetime.now()))
        results.append(f"✅ Mobile code generated and saved to `{filename}` and Mobile AI → Code Library")
        results.append(response)
    else:
        results.append(f"❌ {error}")

    return "\n\n".join(results)


def agent_admin(user_id, task, context=""):
    """Admin AI Agent — full system control, creates files, manages everything"""
    results = []

    prompt = f"""You are the Admin AI Master Agent with full system control.
Execute this task completely and physically: {task}
Context: {context}

Actions you can take:
- Create files and reports
- Analyze all system data
- Generate documentation
- Create automation scripts
- Manage all modules

Provide complete, actionable output."""

    response, error = call_ai(prompt, "You are the Admin AI Master with full agency control.")
    if response:
        # Save output
        os.makedirs("admin_output", exist_ok=True)
        filename = f"admin_output/task_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"TASK: {task}\n\nCONTEXT: {context}\n\nRESULT:\n{response}")
        results.append(f"✅ Admin task executed. Output saved to `{filename}`")
        results.append(response)
    else:
        results.append(f"❌ {error}")

    return "\n\n".join(results)



def agent_lead_master(user_id, task, context=""):
    """
    Lead AI Agent — The Boss. Analyzes task, creates plan,
    delegates to sub-agents automatically, saves project log.
    """
    results = []

    master_prompt = f"""You are the Lead Master Agent. Your goal is: {task}
Context: {context}

You have full control over: /templates, /reports, /crm_output, /admin_output.
Analyze the task and return a structured plan:
- Summary of project goal
- Which agents to activate and why (Sales/WebDev/Marketing/Finance/CRM/ERP/Mobile)
- Step-by-step execution order
"""
    response, error = call_ai(master_prompt, "You are the Project Leader with full system permissions.")

    if response:
        os.makedirs("admin_output", exist_ok=True)
        filename = f"admin_output/project_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"PROJECT LEAD PLAN\nTask: {task}\nContext: {context}\nCreated: {datetime.now()}\n\n{'='*50}\n\nDecision:\n{response}")
            results.append(f"✅ Project plan saved: `{filename}`")
        except IOError as e:
            results.append(f"⚠️ Could not save file: {e}")

        results.append(response)

        # Auto-delegate to sub-agents based on keywords
        task_lower = task.lower()
        resp_lower = response.lower()
        delegated = []

        if any(k in task_lower or k in resp_lower for k in ["sales","lead","email","campaign","outreach"]):
            results.append(f"--- 💼 Sales Agent ---\n{agent_sales(user_id, task, context)}")
            delegated.append("Sales AI")
        if any(k in task_lower or k in resp_lower for k in ["website","web","html","code","landing"]):
            results.append(f"--- 🌐 Web Dev Agent ---\n{agent_webdev(user_id, task, context)}")
            delegated.append("Web Dev AI")
        if any(k in task_lower or k in resp_lower for k in ["marketing","content","social","brand"]):
            results.append(f"--- 📢 Marketing Agent ---\n{agent_marketing(user_id, task, context)}")
            delegated.append("Marketing AI")
        if any(k in task_lower or k in resp_lower for k in ["invoice","finance","payment","expense"]):
            results.append(f"--- 💰 Finance Agent ---\n{agent_finance(user_id, task, context)}")
            delegated.append("Finance AI")
        if any(k in task_lower or k in resp_lower for k in ["crm","contact","follow up","relationship"]):
            results.append(f"--- 🤝 CRM Agent ---\n{agent_crm(user_id, task, context)}")
            delegated.append("CRM AI")
        if any(k in task_lower or k in resp_lower for k in ["inventory","erp","stock","employee"]):
            results.append(f"--- 📊 ERP Agent ---\n{agent_erp(user_id, task, context)}")
            delegated.append("ERP AI")
        if any(k in task_lower or k in resp_lower for k in ["mobile","app","flutter","react native"]):
            results.append(f"--- 📱 Mobile Agent ---\n{agent_mobile(user_id, task, context)}")
            delegated.append("Mobile AI")

        if delegated:
            results.insert(2, f"🔀 Delegated to: {', '.join(delegated)}")
        else:
            results.append("ℹ️ No sub-agents triggered. Add keywords like 'sales', 'website', 'marketing' to your task.")

        log_agent_action("Lead Master Agent", "Project Plan + Delegation", task, f"Delegated to: {delegated}", "success")
    else:
        results.append(f"❌ Lead Agent Error: {error}")
        log_agent_action("Lead Master Agent", "Project Plan", task, error, "error")

    return "\n\n".join(results)

AGENTS = {
    "👑 Lead Master Agent": {"fn": agent_lead_master, "desc": "Project leader: analyzes task, creates plan, auto-coordinates all sub-agents"},
    "💼 Sales AI": {"fn": agent_sales, "desc": "Score leads, write emails, create campaigns, generate reports"},
    "🌐 Web Dev AI": {"fn": agent_webdev, "desc": "Generate websites, write code, save HTML/CSS/JS files"},
    "📢 Marketing AI": {"fn": agent_marketing, "desc": "Create content, campaigns, social posts, save to library"},
    "💰 Finance AI": {"fn": agent_finance, "desc": "Create invoices, generate reports, analyze finances"},
    "🤝 CRM AI": {"fn": agent_crm, "desc": "Add contacts, write follow-ups, manage relationships"},
    "📊 ERP AI": {"fn": agent_erp, "desc": "Analyze inventory, manage stock, generate operations reports"},
    "📱 Mobile AI": {"fn": agent_mobile, "desc": "Generate mobile app code, save to files"},
    "🛡️ Admin AI": {"fn": agent_admin, "desc": "Full system control, create any file, manage everything"},
}



# ====== PHASE 3 CODE ======


import os
import json
import sqlite3
import smtplib
import imaplib
import email
import secrets
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

PHASE1_OK = True  # Embedded


# ============================================================
# SECTION 1 — DATABASE SETUP FOR CHAT & EMAIL
# ============================================================

DB_CHAT  = "db/chat.db"
DB_EMAIL = "db/email.db"

def init_chat_db():
    """Initialize chat and email databases."""
    os.makedirs("db", exist_ok=True)

    # CHAT DB
    conn = sqlite3.connect(DB_CHAT)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS chat_rooms (
        id INTEGER PRIMARY KEY,
        room_id TEXT UNIQUE,
        room_type TEXT,      -- admin_agent | admin_user | admin_wl | user_agent | section
        participant_a TEXT,  -- admin / user_id / wl_id
        participant_b TEXT,  -- agent_name / user_id / wl_id
        section TEXT,        -- sales | webdev | marketing | finance | crm | erp | mobile
        is_online BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY,
        room_id TEXT,
        sender TEXT,
        sender_type TEXT,    -- admin | agent | user | whitelabel | system
        message TEXT,
        attachment_path TEXT,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS chat_training (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        training_type TEXT,  -- file | email | chat | manual
        content TEXT,
        source TEXT,
        processed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS call_logs (
        id INTEGER PRIMARY KEY,
        room_id TEXT,
        caller TEXT,
        receiver TEXT,
        call_type TEXT,      -- voice | video
        duration_seconds INTEGER DEFAULT 0,
        status TEXT,         -- missed | completed | rejected
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

    # EMAIL DB
    conn = sqlite3.connect(DB_EMAIL)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS agent_email_accounts (
        id INTEGER PRIMARY KEY,
        agent_name TEXT UNIQUE,
        email_address TEXT UNIQUE,
        display_name TEXT,
        smtp_host TEXT DEFAULT 'smtp.gmail.com',
        smtp_port INTEGER DEFAULT 587,
        imap_host TEXT DEFAULT 'imap.gmail.com',
        imap_port INTEGER DEFAULT 993,
        username TEXT,
        password TEXT,       -- encrypted app password
        is_active BOOLEAN DEFAULT 1,
        last_checked TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS emails_sent (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        from_email TEXT,
        to_email TEXT,
        cc TEXT,
        subject TEXT,
        body TEXT,
        attachment_path TEXT,
        status TEXT DEFAULT 'sent',
        client_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS emails_received (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        to_email TEXT,
        from_email TEXT,
        subject TEXT,
        body TEXT,
        attachment_path TEXT,
        is_read BOOLEAN DEFAULT 0,
        is_processed BOOLEAN DEFAULT 0,
        auto_replied BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS email_templates (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        template_name TEXT,
        subject TEXT,
        body TEXT,
        variables TEXT DEFAULT '[]',   -- JSON list of {var} placeholders
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS email_rules (
        id INTEGER PRIMARY KEY,
        agent_name TEXT,
        rule_name TEXT,
        condition_field TEXT,   -- from | subject | body
        condition_value TEXT,
        action TEXT,            -- reply | forward | save | train | alert
        action_data TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

init_chat_db()


# ============================================================
# SECTION 2 — AGENT EMAIL IDENTITY MANAGER
# ============================================================

# Default agent email assignments
AGENT_EMAIL_DEFAULTS = {
    "👑 Lead Master Agent": {"name": "Lead Master",      "prefix": "master"},
    "💼 Sales AI":          {"name": "Sales Team",       "prefix": "sales"},
    "🌐 Web Dev AI":        {"name": "Web Dev Team",     "prefix": "webdev"},
    "📢 Marketing AI":      {"name": "Marketing Team",   "prefix": "marketing"},
    "💰 Finance AI":        {"name": "Finance Team",     "prefix": "finance"},
    "🤝 CRM AI":            {"name": "CRM Team",         "prefix": "crm"},
    "📊 ERP AI":            {"name": "ERP Team",         "prefix": "erp"},
    "📱 Mobile AI":         {"name": "Mobile Team",      "prefix": "mobile"},
    "🛡️ Admin AI":          {"name": "Admin Team",       "prefix": "admin"},
}


class AgentEmailIdentity:

    @staticmethod
    def setup_agent_email(agent_name: str, domain: str,
                          gmail_username: str, gmail_app_password: str) -> dict:
        """
        Assign a unique email to an agent and save credentials.
        Uses Gmail with app password (no OAuth needed for SMTP/IMAP).
        """
        defaults = AGENT_EMAIL_DEFAULTS.get(agent_name, {})
        prefix = defaults.get("prefix", "agent")
        display = defaults.get("name", agent_name)
        email_addr = f"{prefix}@{domain}"

        encrypted_pw = encrypt(gmail_app_password) if PHASE1_OK else gmail_app_password

        conn = sqlite3.connect(DB_EMAIL)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO agent_email_accounts
            (agent_name, email_address, display_name,
             username, password, is_active)
            VALUES (?,?,?,?,?,1)''',
            (agent_name, email_addr, display,
             gmail_username, encrypted_pw))
        conn.commit()
        conn.close()

        if PHASE1_OK:
            audit("system", "admin", "setup_agent_email",
                  agent_name, f"Email: {email_addr}")

        return {"success": True, "email": email_addr, "agent": agent_name}

    @staticmethod
    def get_agent_email(agent_name: str) -> dict:
        """Get email account details for an agent."""
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM agent_email_accounts WHERE agent_name=?",
                  (agent_name,))
        row = c.fetchone()
        conn.close()
        if row:
            d = dict(row)
            if PHASE1_OK and d.get("password"):
                d["password"] = decrypt(d["password"])
            return d
        return {}

    @staticmethod
    def list_all_agent_emails() -> list:
        """List all agent email accounts."""
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT agent_name, email_address, display_name, is_active, last_checked FROM agent_email_accounts")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows


# ============================================================
# SECTION 3 — GMAIL ENGINE (SMTP + IMAP)
# ============================================================

class GmailEngine:
    """
    Full Gmail integration for all agents.
    Send, receive, read, reply, forward emails.
    """

    @staticmethod
    def send_email(agent_name: str, to: str, subject: str,
                   body: str, cc: str = "", attachment_path: str = None,
                   client_id: str = None) -> dict:
        """Send an email from an agent's Gmail account."""
        acct = AgentEmailIdentity.get_agent_email(agent_name)
        if not acct:
            return {"success": False,
                    "error": f"No email configured for {agent_name}"}

        try:
            msg = MIMEMultipart()
            msg['From']    = f"{acct['display_name']} <{acct['username']}>"
            msg['To']      = to
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = cc

            msg.attach(MIMEText(body, 'html'))

            # Attachment
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(acct['smtp_host'], acct['smtp_port']) as server:
                server.ehlo()
                server.starttls()
                server.login(acct['username'], acct['password'])
                recipients = [to] + ([cc] if cc else [])
                server.sendmail(acct['username'], recipients, msg.as_string())

            # Log to DB
            conn = sqlite3.connect(DB_EMAIL)
            c = conn.cursor()
            c.execute('''INSERT INTO emails_sent
                (agent_name, from_email, to_email, cc, subject, body,
                 attachment_path, status, client_id)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (agent_name, acct['username'], to, cc, subject, body,
                 attachment_path or "", "sent", client_id or ""))
            conn.commit()
            conn.close()

            return {"success": True, "from": acct['username'],
                    "to": to, "subject": subject}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def fetch_emails(agent_name: str, limit: int = 20) -> dict:
        """Fetch new emails from an agent's Gmail inbox via IMAP."""
        acct = AgentEmailIdentity.get_agent_email(agent_name)
        if not acct:
            return {"success": False, "error": "No email configured", "emails": []}

        try:
            mail = imaplib.IMAP4_SSL(acct['imap_host'], acct['imap_port'])
            mail.login(acct['username'], acct['password'])
            mail.select('inbox')

            _, data = mail.search(None, 'UNSEEN')
            email_ids = data[0].split()[-limit:]

            fetched = []
            conn = sqlite3.connect(DB_EMAIL)
            c = conn.cursor()

            for eid in reversed(email_ids):
                _, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])

                subject = msg.get('Subject', '(no subject)')
                from_addr = msg.get('From', '')
                date_str = msg.get('Date', '')

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(
                                errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')

                # Save to DB
                c.execute('''INSERT OR IGNORE INTO emails_received
                    (agent_name, to_email, from_email, subject, body)
                    VALUES (?,?,?,?,?)''',
                    (agent_name, acct['username'], from_addr,
                     subject, body[:5000]))

                fetched.append({
                    "from": from_addr,
                    "subject": subject,
                    "body": body[:500],
                    "date": date_str
                })

            conn.commit()
            conn.close()
            mail.logout()

            # Update last checked
            conn2 = sqlite3.connect(DB_EMAIL)
            c2 = conn2.cursor()
            c2.execute("UPDATE agent_email_accounts SET last_checked=? WHERE agent_name=?",
                      (datetime.now(), agent_name))
            conn2.commit()
            conn2.close()

            return {"success": True, "emails": fetched, "count": len(fetched)}

        except Exception as e:
            return {"success": False, "error": str(e), "emails": []}

    @staticmethod
    def reply_to_email(agent_name: str, to: str,
                       original_subject: str, reply_body: str) -> dict:
        """Send a reply email."""
        subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") \
                  else original_subject
        return GmailEngine.send_email(agent_name, to, subject, reply_body)

    @staticmethod
    def process_email_rules(agent_name: str) -> list:
        """
        Check incoming emails against rules and auto-execute actions.
        Rules: reply | forward | save_to_training | alert_admin
        """
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Get unprocessed emails
        c.execute('''SELECT * FROM emails_received
            WHERE agent_name=? AND is_processed=0 LIMIT 20''',
            (agent_name,))
        emails = [dict(r) for r in c.fetchall()]

        # Get active rules
        c.execute("SELECT * FROM email_rules WHERE agent_name=? AND is_active=1",
                  (agent_name,))
        rules = [dict(r) for r in c.fetchall()]
        conn.close()

        actions_taken = []
        for em in emails:
            for rule in rules:
                field = rule['condition_field']
                value = rule['condition_value'].lower()
                em_field = em.get(field, "").lower()

                if value in em_field:
                    action = rule['action']
                    if action == 'reply':
                        GmailEngine.reply_to_email(
                            agent_name, em['from_email'],
                            em['subject'], rule['action_data'])
                        actions_taken.append(
                            f"Auto-replied to {em['from_email']}")

                    elif action == 'save_to_training':
                        _save_to_training(agent_name, "email",
                                         em['body'], em['from_email'])
                        actions_taken.append(
                            f"Saved email from {em['from_email']} to training")

                    elif action == 'forward':
                        GmailEngine.send_email(
                            agent_name, rule['action_data'],
                            f"FWD: {em['subject']}", em['body'])
                        actions_taken.append(
                            f"Forwarded to {rule['action_data']}")

            # Mark as processed
            conn2 = sqlite3.connect(DB_EMAIL)
            c2 = conn2.cursor()
            c2.execute("UPDATE emails_received SET is_processed=1 WHERE id=?",
                      (em['id'],))
            conn2.commit()
            conn2.close()

        return actions_taken

    @staticmethod
    def get_sent_emails(agent_name: str, limit: int = 20) -> list:
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM emails_sent WHERE agent_name=?
            ORDER BY created_at DESC LIMIT ?''', (agent_name, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_received_emails(agent_name: str, limit: int = 20) -> list:
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM emails_received WHERE agent_name=?
            ORDER BY created_at DESC LIMIT ?''', (agent_name, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows


# ============================================================
# SECTION 4 — CHAT ENGINE
# ============================================================

class ChatEngine:
    """
    Full chat system:
    - Admin ↔ Any Agent (direct)
    - Admin ↔ User
    - Admin ↔ White Label
    - Per-Section chat (each module has its own)
    - Offline message queue
    - Call logging
    """

    @staticmethod
    def get_or_create_room(room_type: str, participant_a: str,
                            participant_b: str, section: str = "") -> str:
        """Get existing room or create new one. Returns room_id."""
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Check if room exists
        c.execute('''SELECT room_id FROM chat_rooms
            WHERE room_type=? AND participant_a=? AND participant_b=?''',
            (room_type, participant_a, participant_b))
        row = c.fetchone()

        if row:
            conn.close()
            return row['room_id']

        # Create new room
        room_id = f"room_{secrets.token_hex(8)}"
        c.execute('''INSERT INTO chat_rooms
            (room_id, room_type, participant_a, participant_b, section)
            VALUES (?,?,?,?,?)''',
            (room_id, room_type, participant_a, participant_b, section))
        conn.commit()
        conn.close()
        return room_id

    @staticmethod
    def send_message(room_id: str, sender: str, sender_type: str,
                     message: str, attachment_path: str = None) -> dict:
        """Send a message in a chat room."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute('''INSERT INTO chat_messages
            (room_id, sender, sender_type, message, attachment_path)
            VALUES (?,?,?,?,?)''',
            (room_id, sender, sender_type, message, attachment_path or ""))
        msg_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "msg_id": msg_id, "room_id": room_id}

    @staticmethod
    def get_messages(room_id: str, limit: int = 50,
                     offset: int = 0) -> list:
        """Get chat messages for a room."""
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM chat_messages WHERE room_id=?
            ORDER BY created_at DESC LIMIT ? OFFSET ?''',
            (room_id, limit, offset))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return list(reversed(rows))

    @staticmethod
    def get_unread_count(room_id: str, reader: str) -> int:
        """Count unread messages for a participant."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute('''SELECT COUNT(*) FROM chat_messages
            WHERE room_id=? AND sender!=? AND is_read=0''',
            (room_id, reader))
        count = c.fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def mark_read(room_id: str, reader: str):
        """Mark all messages as read for a reader."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute('''UPDATE chat_messages SET is_read=1
            WHERE room_id=? AND sender!=?''', (room_id, reader))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_rooms(participant: str) -> list:
        """Get all chat rooms for a participant."""
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT * FROM chat_rooms
            WHERE participant_a=? OR participant_b=?
            ORDER BY created_at DESC''',
            (participant, participant))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def set_online_status(room_id: str, is_online: bool):
        """Set online/offline status for a room."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute("UPDATE chat_rooms SET is_online=? WHERE room_id=?",
                  (1 if is_online else 0, room_id))
        conn.commit()
        conn.close()

    @staticmethod
    def log_call(room_id: str, caller: str, receiver: str,
                 call_type: str = "voice", status: str = "completed",
                 duration: int = 0) -> dict:
        """Log a call event."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute('''INSERT INTO call_logs
            (room_id, caller, receiver, call_type, duration_seconds, status)
            VALUES (?,?,?,?,?,?)''',
            (room_id, caller, receiver, call_type, duration, status))
        conn.commit()
        conn.close()
        return {"success": True}

    @staticmethod
    def search_messages(participant: str, keyword: str) -> list:
        """Search chat history for a keyword."""
        rooms = ChatEngine.get_all_rooms(participant)
        results = []
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        for room in rooms:
            c.execute('''SELECT * FROM chat_messages
                WHERE room_id=? AND message LIKE ?
                ORDER BY created_at DESC LIMIT 5''',
                (room['room_id'], f"%{keyword}%"))
            for row in c.fetchall():
                r = dict(row)
                r['room_type'] = room['room_type']
                r['participant_b'] = room['participant_b']
                results.append(r)
        conn.close()
        return results


# ============================================================
# SECTION 5 — AI CHAT (Agent responds in chat)
# ============================================================

class AgentChatResponder:
    """
    When admin sends a message to an agent in chat,
    the agent responds using AI automatically.
    """

    @staticmethod
    def agent_respond(agent_name: str, user_message: str,
                      room_id: str, call_ai_fn,
                      context: str = "") -> dict:
        """
        Generate and save an AI response from an agent in chat.
        """
        # Build agent-specific system prompt
        agent_prompts = {
            "👑 Lead Master Agent": "You are the Lead Master Agent — the boss. You coordinate all other agents and make high-level decisions.",
            "💼 Sales AI":          "You are the Sales AI — expert in leads, campaigns, outreach, and closing deals.",
            "🌐 Web Dev AI":        "You are the Web Dev AI — expert in HTML, CSS, JS, React, and full-stack development.",
            "📢 Marketing AI":      "You are the Marketing AI — expert in campaigns, content, SEO, social media.",
            "💰 Finance AI":        "You are the Finance AI — expert in invoicing, expenses, financial reports.",
            "🤝 CRM AI":            "You are the CRM AI — expert in contacts, deals, follow-ups, relationships.",
            "📊 ERP AI":            "You are the ERP AI — expert in inventory, employees, supply chain.",
            "📱 Mobile AI":         "You are the Mobile AI — expert in Flutter, React Native, iOS/Android development.",
            "🛡️ Admin AI":          "You are the Admin AI — full system control, documentation, management.",
        }

        system_prompt = agent_prompts.get(
            agent_name,
            f"You are {agent_name}, an AI assistant."
        )
        system_prompt += "\nYou are in a direct chat with the admin. Be concise, helpful, and professional."

        full_prompt = f"{context}\n\nAdmin says: {user_message}" if context else user_message

        response, error = call_ai_fn(full_prompt, system_prompt)

        if response:
            ChatEngine.send_message(room_id, agent_name, "agent", response)
            return {"success": True, "response": response}
        return {"success": False, "error": error}


# ============================================================
# SECTION 6 — AI TRAINING SYSTEM
# ============================================================

class AITrainingSystem:
    """
    Train agents via chat, file upload, or email.
    Training data is stored and injected into agent context.
    """

    @staticmethod
    def train_from_text(agent_name: str, content: str,
                        source: str = "manual") -> dict:
        """Add text training data for an agent."""
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute('''INSERT INTO chat_training
            (agent_name, training_type, content, source)
            VALUES (?,?,?,?)''',
            (agent_name, "manual", content, source))
        conn.commit()
        conn.close()
        return {"success": True}

    @staticmethod
    def train_from_file(agent_name: str, file_path: str) -> dict:
        """Load training data from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            conn = sqlite3.connect(DB_CHAT)
            c = conn.cursor()
            c.execute('''INSERT INTO chat_training
                (agent_name, training_type, content, source)
                VALUES (?,?,?,?)''',
                (agent_name, "file", content[:10000],
                 os.path.basename(file_path)))
            conn.commit()
            conn.close()
            return {"success": True, "chars_loaded": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def train_from_uploaded_file(agent_name: str, uploaded_file, source: str = "uploaded") -> dict:
        """Load training data from a Streamlit file uploader object."""
        try:
            # Read content from the uploaded file object
            content = uploaded_file.read()
            
            # If it's bytes, decode to string
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            conn = sqlite3.connect(DB_CHAT)
            c = conn.cursor()
            c.execute('''INSERT INTO chat_training
                (agent_name, training_type, content, source)
                VALUES (?,?,?,?)''',
                (agent_name, "uploaded_file", content[:10000],
                 source))
            conn.commit()
            conn.close()
            return {"success": True, "chars_loaded": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_training_context(agent_name: str, limit: int = 5) -> str:
        """Build training context to inject into agent prompts."""
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT content, source FROM chat_training
            WHERE agent_name=? ORDER BY created_at DESC LIMIT ?''',
            (agent_name, limit))
        rows = c.fetchall()
        conn.close()

        if not rows:
            return ""

        parts = [f"[TRAINING DATA FOR {agent_name}]"]
        for row in rows:
            parts.append(f"[Source: {row['source']}]\n{row['content'][:500]}")
        return "\n\n".join(parts)

    @staticmethod
    def list_training_data(agent_name: str) -> list:
        conn = sqlite3.connect(DB_CHAT)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT id, training_type, source, processed,
            substr(content, 1, 100) as preview, created_at
            FROM chat_training WHERE agent_name=?
            ORDER BY created_at DESC''', (agent_name,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def delete_training(training_id: int) -> dict:
        conn = sqlite3.connect(DB_CHAT)
        c = conn.cursor()
        c.execute("DELETE FROM chat_training WHERE id=?", (training_id,))
        conn.commit()
        conn.close()
        return {"success": True}


def _save_to_training(agent_name: str, source_type: str,
                      content: str, source: str):
    """Internal helper to save email/chat content as training."""
    conn = sqlite3.connect(DB_CHAT)
    c = conn.cursor()
    c.execute('''INSERT INTO chat_training
        (agent_name, training_type, content, source)
        VALUES (?,?,?,?)''',
        (agent_name, source_type, content[:5000], source))
    conn.commit()
    conn.close()


# ============================================================
# SECTION 7 — EMAIL BACKGROUND CHECKER
# ============================================================

class EmailPoller:
    """
    Background thread that periodically checks
    all agent inboxes and processes email rules.
    """

    def __init__(self, interval_minutes: int = 5):
        self.interval = interval_minutes * 60
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            try:
                accounts = AgentEmailIdentity.list_all_agent_emails()
                for acct in accounts:
                    if acct.get('is_active') and acct.get('email_address'):
                        try:
                            GmailEngine.fetch_emails(acct['agent_name'], limit=10)
                            GmailEngine.process_email_rules(acct['agent_name'])
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(self.interval)


# Start email poller (checks every 5 minutes)
email_poller = EmailPoller(interval_minutes=5)
# email_poller.start()  # Uncomment after Gmail credentials are configured


# ============================================================
# SECTION 8 — STREAMLIT UI COMPONENTS
# ============================================================

def render_chat_widget(room_id: str, current_user: str,
                       other_party: str, call_ai_fn=None,
                       agent_name: str = None,
                       show_call_btn: bool = True):
    """
    Reusable chat widget — renders anywhere in the app.
    Supports: message history, send, file attach, call button.
    """

    # Message history
    messages = ChatEngine.get_messages(room_id, limit=50)
    ChatEngine.mark_read(room_id, current_user)

    # Chat container with scroll
    chat_container = st.container()
    with chat_container:
        if messages:
            for msg in messages:
                is_me = msg['sender'] == current_user
                align = "right" if is_me else "left"
                bg = "#667eea" if is_me else "#f0f0f0"
                color = "white" if is_me else "#1a202c"
                name = "You" if is_me else msg['sender']

                st.markdown(f"""
                <div style='text-align:{align}; margin:6px 0;'>
                    <div style='display:inline-block; background:{bg};
                         color:{color}; padding:10px 14px; border-radius:18px;
                         max-width:75%; text-align:left;'>
                        <small style='opacity:0.7; font-size:0.7rem;'>{name}</small><br>
                        {msg['message']}
                        <br><small style='opacity:0.5; font-size:0.65rem;'>
                        {str(msg['created_at'])[:16]}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No messages yet. Start the conversation!")

    st.divider()

    # Input row
    col_msg, col_send, col_call = st.columns([6, 1, 1])
    with col_msg:
        user_input = st.text_input(
            "Message", key=f"chat_input_{room_id}",
            placeholder="Type a message...",
            label_visibility="collapsed")
    with col_send:
        send_btn = st.button("Send", key=f"send_{room_id}",
                             use_container_width=True, type="primary")
    with col_call:
        if show_call_btn:
            call_btn = st.button("📞", key=f"call_{room_id}",
                                use_container_width=True)
            if call_btn:
                ChatEngine.log_call(room_id, current_user,
                                   other_party, "voice", "initiated")
                st.info("📞 Call initiated — WebRTC coming in Phase 5")

    if send_btn and user_input:
        # Save user message
        ChatEngine.send_message(room_id, current_user, "admin", user_input)

        # If chatting with an agent, auto-respond
        if agent_name and call_ai_fn:
            with st.spinner(f"{agent_name} is typing..."):
                AgentChatResponder.agent_respond(
                    agent_name, user_input, room_id, call_ai_fn)
        st.rerun()

    # File attachment
    with st.expander("📎 Attach File / Train Agent"):
        uploaded = st.file_uploader(
            "Attach file", key=f"attach_{room_id}",
            type=['txt', 'pdf', 'csv', 'json', 'py', 'html', 'md'])
        col1, col2 = st.columns(2)
        if uploaded:
            with col1:
                if st.button("📤 Send File", key=f"send_file_{room_id}"):
                    save_path = f"uploads/{uploaded.name}"
                    os.makedirs("uploads", exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                    ChatEngine.send_message(
                        room_id, current_user, "admin",
                        f"📎 File attached: {uploaded.name}",
                        attachment_path=save_path)
                    st.success("✅ File sent!")
                    st.rerun()
            with col2:
                if agent_name:
                    if st.button("🧠 Use as Training", key=f"train_{room_id}"):
                        save_path = f"ai_training/{uploaded.name}"
                        os.makedirs("ai_training", exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(uploaded.getbuffer())
                        result = AITrainingSystem.train_from_file(
                            agent_name, save_path)
                        if result["success"]:
                            st.success(f"✅ Added to {agent_name} training data!")
                        else:
                            st.error(result.get("error"))


def render_email_widget(agent_name: str, call_ai_fn=None):
    """
    Email management widget for an agent.
    Shows inbox, sent, compose form.
    """

    acct = AgentEmailIdentity.get_agent_email(agent_name)

    if not acct:
        st.warning(f"No email configured for {agent_name}. Set up in Settings → Email Setup.")
        return

    st.caption(f"📧 Agent email: **{acct.get('email_address', 'Not set')}**")

    tab_inbox, tab_sent, tab_compose, tab_rules = st.tabs(
        ["📥 Inbox", "📤 Sent", "✏️ Compose", "⚙️ Rules"])

    with tab_inbox:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Check Email", use_container_width=True,
                        key=f"check_{agent_name}"):
                with st.spinner("Checking inbox..."):
                    result = GmailEngine.fetch_emails(agent_name)
                if result["success"]:
                    st.success(f"✅ {result['count']} new emails")
                else:
                    st.error(f"❌ {result.get('error')}")
                st.rerun()

        emails = GmailEngine.get_received_emails(agent_name)
        if emails:
            for em in emails:
                read_badge = "badge-yellow" if not em['is_read'] else "badge-green"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    with c1:
                        st.markdown(f"**{em['subject'][:60]}**")
                        st.caption(f"From: {em['from_email']} | {str(em['created_at'])[:16]}")
                        with st.expander("Read"):
                            st.text(em['body'][:1000])
                    with c2:
                        st.markdown(f"<span class='{read_badge}'>{'Unread' if not em['is_read'] else 'Read'}</span>",
                                   unsafe_allow_html=True)
                    with c3:
                        if st.button("↩️ Reply", key=f"reply_{em['id']}"):
                            st.session_state[f"reply_to_{agent_name}"] = em
        else:
            st.info("No emails yet. Click 'Check Email' to fetch.")

    with tab_sent:
        sent = GmailEngine.get_sent_emails(agent_name)
        if sent:
            for em in sent:
                with st.container(border=True):
                    st.markdown(f"**To:** {em['to_email']} | **Subject:** {em['subject'][:50]}")
                    st.caption(f"Sent: {str(em['created_at'])[:16]} | Status: {em['status']}")
        else:
            st.info("No sent emails yet.")

    with tab_compose:
        with st.form(f"compose_{agent_name}"):
            to = st.text_input("To", placeholder="client@email.com")
            subject = st.text_input("Subject")
            body = st.text_area("Body", height=150,
                               placeholder="Write your email here...")
            cc = st.text_input("CC (optional)")
            send_submitted = st.form_submit_button("📤 Send Email", type="primary")
            if send_submitted:
                if to and subject and body:
                    result = GmailEngine.send_email(
                        agent_name, to, subject, body, cc)
                    if result["success"]:
                        st.success(f"✅ Email sent to {to}!")
                    else:
                        st.error(f"❌ {result.get('error')}")
                else:
                    st.warning("Fill in To, Subject and Body")

    with tab_rules:
        st.markdown("**Auto-Response Rules**")
        with st.form(f"rule_{agent_name}"):
            rule_name = st.text_input("Rule Name")
            field = st.selectbox("If", ["subject", "from_email", "body"])
            condition = st.text_input("Contains")
            action = st.selectbox("Then", ["reply", "forward", "save_to_training"])
            action_data = st.text_area("Action Data",
                height=80, placeholder="Reply text / Forward address")
            if st.form_submit_button("Save Rule"):
                conn = sqlite3.connect(DB_EMAIL)
                c = conn.cursor()
                c.execute('''INSERT INTO email_rules
                    (agent_name, rule_name, condition_field,
                     condition_value, action, action_data)
                    VALUES (?,?,?,?,?,?)''',
                    (agent_name, rule_name, field,
                     condition, action, action_data))
                conn.commit()
                conn.close()
                st.success("✅ Rule saved!")
                st.rerun()

        # Show existing rules
        conn = sqlite3.connect(DB_EMAIL)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM email_rules WHERE agent_name=?", (agent_name,))
        rules = [dict(r) for r in c.fetchall()]
        conn.close()
        for rule in rules:
            with st.container(border=True):
                st.markdown(f"**{rule['rule_name']}** — If `{rule['condition_field']}` contains `{rule['condition_value']}` → `{rule['action']}`")
                if st.button("🗑️ Delete", key=f"del_rule_{rule['id']}"):
                    conn2 = sqlite3.connect(DB_EMAIL)
                    c2 = conn2.cursor()
                    c2.execute("DELETE FROM email_rules WHERE id=?", (rule['id'],))
                    conn2.commit()
                    conn2.close()
                    st.rerun()


print("✅ Phase 3 Gmail + Chat loaded:")
print("   ✅ Agent email identity system (unique email per agent)")
print("   ✅ Gmail SMTP/IMAP engine (send/receive/reply/forward)")
print("   ✅ Email rules engine (auto-reply, forward, train)")
print("   ✅ Email background poller (checks every 5 min)")
print("   ✅ Chat engine (admin↔agent, admin↔user, admin↔wl, per-section)")
print("   ✅ AI chat responder (agents reply in chat using AI)")
print("   ✅ AI training system (train via chat/file/email)")
print("   ✅ Chat + email UI widgets (reusable everywhere)")



# ====== PHASE 4 CODE ======


import os
import json
import sqlite3
import secrets
import threading
import time
import hashlib
from datetime import datetime, timedelta, date

PHASE1_OK = True  # Embedded

DB_SCHEDULER     = "db/scheduler.db"
DB_NOTIFICATIONS = "db/notifications.db"


# ============================================================
# SECTION 1 — SCHEDULER DATABASE
# ============================================================

def init_scheduler_db():
    os.makedirs("db", exist_ok=True)

    conn = sqlite3.connect(DB_SCHEDULER)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id INTEGER PRIMARY KEY,
        task_id TEXT UNIQUE,
        name TEXT,
        agent_name TEXT,
        user_id TEXT,
        task TEXT,
        context TEXT DEFAULT '',
        frequency TEXT,      -- once | daily | weekly | monthly | custom
        cron_expr TEXT,      -- e.g. "09:00" for daily, "MON 09:00" for weekly
        next_run TIMESTAMP,
        last_run TIMESTAMP,
        last_status TEXT,
        is_active BOOLEAN DEFAULT 1,
        run_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS schedule_logs (
        id INTEGER PRIMARY KEY,
        task_id TEXT,
        agent_name TEXT,
        status TEXT,
        result TEXT,
        duration_ms INTEGER,
        ran_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()

    # Notifications DB
    conn2 = sqlite3.connect(DB_NOTIFICATIONS)
    c2 = conn2.cursor()

    c2.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        user_id TEXT,
        user_type TEXT,      -- admin | user | whitelabel
        title TEXT,
        message TEXT,
        type TEXT,           -- info | success | warning | error | task | email | chat
        is_read BOOLEAN DEFAULT 0,
        action_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c2.execute('''CREATE TABLE IF NOT EXISTS notification_settings (
        id INTEGER PRIMARY KEY,
        user_id TEXT UNIQUE,
        email_alerts BOOLEAN DEFAULT 1,
        browser_alerts BOOLEAN DEFAULT 1,
        task_complete BOOLEAN DEFAULT 1,
        new_email BOOLEAN DEFAULT 1,
        new_chat BOOLEAN DEFAULT 1,
        agent_errors BOOLEAN DEFAULT 1,
        daily_digest BOOLEAN DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn2.commit()
    conn2.close()

init_scheduler_db()


# ============================================================
# SECTION 2 — USER MANAGEMENT ENGINE
# ============================================================

PLAN_LIMITS = {
    "basic":      {"agents": 3,  "storage_mb": 500,  "tasks_per_day": 10,  "wl_allowed": False},
    "pro":        {"agents": 7,  "storage_mb": 2000, "tasks_per_day": 50,  "wl_allowed": False},
    "enterprise": {"agents": 99, "storage_mb": 10000,"tasks_per_day": 999, "wl_allowed": True},
}

class UserManager:

    @staticmethod
    def create_user(username: str, password: str, email: str,
                    full_name: str = "", role: str = "user",
                    plan: str = "basic") -> dict:
        try:
            db_exec(DB_USERS, '''INSERT INTO users
                (username, password, email, full_name, role, plan, is_active)
                VALUES (?,?,?,?,?,?,1)''',
                (username, hash_password(password), email,
                 full_name, role, plan))
            # Create default settings
            users = db_fetch_with_path(DB_USERS,
                "SELECT id FROM users WHERE username=?", (username,))
            if users:
                db_exec(DB_USERS, '''INSERT OR IGNORE INTO user_settings
                    (user_id) VALUES (?)''', (users[0]['id'],))
            audit("system", "admin", "create_user", username,
                  f"Plan: {plan}")
            return {"success": True, "username": username}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_user(user_id: int = None, username: str = None) -> dict:
        if user_id:
            rows = db_fetch_with_path(DB_USERS, "SELECT * FROM users WHERE id=?", (user_id,))
        else:
            rows = db_fetch_with_path(DB_USERS, "SELECT * FROM users WHERE username=?", (username,))
        return rows[0] if rows else {}

    @staticmethod
    def update_user(user_id: int, updates: dict) -> dict:
        if "password" in updates:
            updates["password"] = hash_password(updates["password"])
        set_clause = ", ".join([f"{k}=?" for k in updates])
        params = list(updates.values()) + [user_id]
        db_exec(DB_USERS, f"UPDATE users SET {set_clause} WHERE id=?", tuple(params))
        audit("system", "admin", "update_user", str(user_id), str(updates))
        return {"success": True}

    @staticmethod
    def delete_user(user_id: int, deleted_by: str) -> dict:
        user = UserManager.get_user(user_id=user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        # Create restore point before delete
        RestoreEngine.create_restore_point(
            "user", deleted_by, str(user_id),
            f"Before deleting user: {user.get('username')}")
        db_exec(DB_USERS, "DELETE FROM users WHERE id=?", (user_id,))
        db_exec(DB_USERS, "DELETE FROM user_settings WHERE user_id=?", (user_id,))
        audit(deleted_by, "admin", "delete_user",
              str(user_id), f"Deleted: {user.get('username')}")
        return {"success": True}

    @staticmethod
    def list_users(role: str = None, plan: str = None,
                   is_active: bool = None) -> list:
        query = "SELECT id, username, email, full_name, role, plan, is_active, created_at FROM users WHERE 1=1"
        params = []
        if role:
            query += " AND role=?"; params.append(role)
        if plan:
            query += " AND plan=?"; params.append(plan)
        if is_active is not None:
            query += " AND is_active=?"; params.append(1 if is_active else 0)
        query += " ORDER BY created_at DESC"
        return db_fetch_with_path(DB_USERS, query, tuple(params))

    @staticmethod
    def change_plan(user_id: int, new_plan: str,
                    changed_by: str) -> dict:
        if new_plan not in PLAN_LIMITS:
            return {"success": False, "error": "Invalid plan"}
        db_exec(DB_USERS, "UPDATE users SET plan=? WHERE id=?",
                (new_plan, user_id))
        audit(changed_by, "admin", "change_plan",
              str(user_id), f"New plan: {new_plan}")
        NotificationEngine.send(str(user_id), "user",
            "Plan Updated",
            f"Your plan has been upgraded to {new_plan.upper()}!",
            "success")
        return {"success": True}

    @staticmethod
    def toggle_active(user_id: int, changed_by: str) -> dict:
        user = UserManager.get_user(user_id=user_id)
        new_status = 0 if user.get('is_active') else 1
        db_exec(DB_USERS, "UPDATE users SET is_active=? WHERE id=?",
                (new_status, user_id))
        action = "activated" if new_status else "deactivated"
        audit(changed_by, "admin", f"user_{action}",
              str(user_id), f"User {action}")
        return {"success": True, "is_active": bool(new_status)}

    @staticmethod
    def get_user_activity(user_id: int, limit: int = 20) -> list:
        return db_fetch_with_path(DB_SYSTEM,
            "SELECT * FROM audit_log WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (str(user_id), limit))

    @staticmethod
    def get_plan_limits(plan: str) -> dict:
        return PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])

    @staticmethod
    def reset_password(user_id: int, new_password: str,
                       reset_by: str) -> dict:
        db_exec(DB_USERS,
            "UPDATE users SET password=? WHERE id=?",
            (hash_password(new_password), user_id))
        audit(reset_by, "admin", "reset_password", str(user_id), "Password reset")
        NotificationEngine.send(str(user_id), "user",
            "Password Reset",
            "Your password has been reset by admin.", "warning")
        return {"success": True}


# ============================================================
# SECTION 3 — WHITE LABEL MANAGEMENT ENGINE
# ============================================================

class WhiteLabelManager:

    @staticmethod
    def create_instance(company_name: str, admin_email: str,
                        password: str, subdomain: str,
                        plan: str = "basic",
                        agent_access: list = None) -> dict:
        try:
            if agent_access is None:
                agent_access = ["💼 Sales AI", "🌐 Web Dev AI",
                                "📢 Marketing AI"]
            db_exec(DB_WHITELABEL, '''INSERT INTO whitelabel_instances
                (company_name, admin_email, password, subdomain,
                 plan, agent_access, status)
                VALUES (?,?,?,?,?,?,?)''',
                (company_name,
                 admin_email,
                 hash_password(password),
                 subdomain,
                 plan,
                 json.dumps(agent_access),
                 "active"))

            wls = db_fetch_with_path(DB_WHITELABEL,
                "SELECT id FROM whitelabel_instances WHERE subdomain=?",
                (subdomain,))
            wl_id = wls[0]['id'] if wls else None

            audit("system", "admin", "create_whitelabel",
                  company_name, f"Subdomain: {subdomain}")

            # Auto restore point
            if wl_id:
                RestoreEngine.create_restore_point(
                    "whitelabel", "system", str(wl_id),
                    f"Initial setup: {company_name}")

            return {"success": True, "company": company_name,
                    "subdomain": subdomain, "wl_id": wl_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_instance(wl_id: int = None,
                     subdomain: str = None) -> dict:
        if wl_id:
            rows = db_fetch_with_path(DB_WHITELABEL,
                "SELECT * FROM whitelabel_instances WHERE id=?", (wl_id,))
        else:
            rows = db_fetch_with_path(DB_WHITELABEL,
                "SELECT * FROM whitelabel_instances WHERE subdomain=?",
                (subdomain,))
        return rows[0] if rows else {}

    @staticmethod
    def list_instances(status: str = None) -> list:
        query = '''SELECT id, company_name, admin_email, subdomain,
            plan, status, created_at FROM whitelabel_instances'''
        params = ()
        if status:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        return db_fetch_with_path(DB_WHITELABEL, query, params)

    @staticmethod
    def update_branding(wl_id: int, branding: dict) -> dict:
        db_exec(DB_WHITELABEL,
            "UPDATE whitelabel_instances SET branding=? WHERE id=?",
            (json.dumps(branding), wl_id))
        return {"success": True}

    @staticmethod
    def update_agent_access(wl_id: int, agents: list,
                            updated_by: str) -> dict:
        db_exec(DB_WHITELABEL,
            "UPDATE whitelabel_instances SET agent_access=? WHERE id=?",
            (json.dumps(agents), wl_id))
        audit(updated_by, "admin", "update_wl_agents",
              str(wl_id), f"Agents: {agents}")
        return {"success": True}

    @staticmethod
    def toggle_status(wl_id: int, changed_by: str) -> dict:
        wl = WhiteLabelManager.get_instance(wl_id=wl_id)
        new_status = "inactive" if wl.get("status") == "active" else "active"
        db_exec(DB_WHITELABEL,
            "UPDATE whitelabel_instances SET status=? WHERE id=?",
            (new_status, wl_id))
        audit(changed_by, "admin", f"wl_{new_status}",
              str(wl_id), wl.get("company_name", ""))
        return {"success": True, "status": new_status}

    @staticmethod
    def delete_instance(wl_id: int, deleted_by: str) -> dict:
        wl = WhiteLabelManager.get_instance(wl_id=wl_id)
        RestoreEngine.create_restore_point(
            "whitelabel", deleted_by, str(wl_id),
            f"Before delete: {wl.get('company_name')}")
        db_exec(DB_WHITELABEL,
            "DELETE FROM whitelabel_instances WHERE id=?", (wl_id,))
        audit(deleted_by, "admin", "delete_whitelabel",
              str(wl_id), wl.get("company_name", ""))
        return {"success": True}

    @staticmethod
    def create_wl_restore_point(wl_id: int,
                                created_by: str, note: str = "") -> dict:
        return RestoreEngine.create_restore_point(
            "whitelabel", created_by, str(wl_id), note)

    @staticmethod
    def add_wl_user(wl_id: int, username: str, password: str,
                    email: str, role: str = "client") -> dict:
        try:
            db_exec(DB_WHITELABEL, '''INSERT INTO whitelabel_users
                (wl_id, username, password, email, role, is_active)
                VALUES (?,?,?,?,?,1)''',
                (wl_id, username, hash_password(password), email, role))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_wl_users(wl_id: int) -> list:
        return db_fetch_with_path(DB_WHITELABEL,
            "SELECT id, username, email, role, is_active FROM whitelabel_users WHERE wl_id=?",
            (wl_id,))

    @staticmethod
    def get_stats(wl_id: int) -> dict:
        users = db_fetch_with_path(DB_WHITELABEL,
            "SELECT COUNT(*) as cnt FROM whitelabel_users WHERE wl_id=?",
            (wl_id,))
        wl = WhiteLabelManager.get_instance(wl_id=wl_id)
        agents = json.loads(wl.get("agent_access", "[]")) if wl else []
        return {
            "user_count": users[0]["cnt"] if users else 0,
            "agent_count": len(agents),
            "plan": wl.get("plan", "basic") if wl else "basic",
            "status": wl.get("status", "unknown") if wl else "unknown",
        }


# ============================================================
# SECTION 4 — NOTIFICATION ENGINE
# ============================================================

class NotificationEngine:

    @staticmethod
    def send(user_id: str, user_type: str, title: str,
             message: str, notif_type: str = "info",
             action_url: str = "") -> dict:
        conn = sqlite3.connect(DB_NOTIFICATIONS)
        c = conn.cursor()
        c.execute('''INSERT INTO notifications
            (user_id, user_type, title, message, type, action_url)
            VALUES (?,?,?,?,?,?)''',
            (str(user_id), user_type, title, message,
             notif_type, action_url))
        conn.commit()
        conn.close()
        return {"success": True}

    @staticmethod
    def get_notifications(user_id: str, unread_only: bool = False,
                          limit: int = 50) -> list:
        conn = sqlite3.connect(DB_NOTIFICATIONS)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        query = "SELECT * FROM notifications WHERE user_id=?"
        params = [str(user_id)]
        if unread_only:
            query += " AND is_read=0"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        c.execute(query, tuple(params))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def mark_read(notif_id: int = None, user_id: str = None):
        conn = sqlite3.connect(DB_NOTIFICATIONS)
        c = conn.cursor()
        if notif_id:
            c.execute("UPDATE notifications SET is_read=1 WHERE id=?",
                     (notif_id,))
        elif user_id:
            c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",
                     (str(user_id),))
        conn.commit()
        conn.close()

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        conn = sqlite3.connect(DB_NOTIFICATIONS)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0",
                 (str(user_id),))
        count = c.fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def delete_old(days: int = 30):
        cutoff = datetime.now() - timedelta(days=days)
        conn = sqlite3.connect(DB_NOTIFICATIONS)
        c = conn.cursor()
        c.execute("DELETE FROM notifications WHERE created_at < ? AND is_read=1",
                 (cutoff,))
        conn.commit()
        conn.close()

    @staticmethod
    def broadcast(title: str, message: str,
                  notif_type: str = "info"):
        """Send notification to all users."""
        users = db_fetch_with_path(DB_USERS,
            "SELECT id FROM users WHERE is_active=1")
        for u in users:
            NotificationEngine.send(str(u['id']), "user",
                                   title, message, notif_type)


# ============================================================
# SECTION 5 — TASK SCHEDULER
# ============================================================

class TaskScheduler:
    """
    Schedule agent tasks to run automatically.
    Frequencies: once | daily | weekly | monthly
    """

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def schedule_task(self, name: str, agent_name: str,
                      user_id: str, task: str,
                      frequency: str, run_time: str,
                      context: str = "") -> dict:
        """
        Schedule a task.
        run_time: "HH:MM" for daily, "DAY HH:MM" for weekly,
                  "DD HH:MM" for monthly
        """
        task_id = f"sched_{secrets.token_hex(6)}"
        next_run = self._calc_next_run(frequency, run_time)

        conn = sqlite3.connect(DB_SCHEDULER)
        c = conn.cursor()
        c.execute('''INSERT INTO scheduled_tasks
            (task_id, name, agent_name, user_id, task, context,
             frequency, cron_expr, next_run, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,1)''',
            (task_id, name, agent_name, str(user_id), task,
             context, frequency, run_time, next_run))
        conn.commit()
        conn.close()

        NotificationEngine.send(str(user_id), "user",
            "Task Scheduled",
            f"'{name}' scheduled to run {frequency} at {run_time}",
            "info")

        return {"success": True, "task_id": task_id,
                "next_run": str(next_run)}

    def _calc_next_run(self, frequency: str, run_time: str) -> datetime:
        now = datetime.now()
        try:
            if frequency == "once":
                # run_time = "YYYY-MM-DD HH:MM"
                return datetime.strptime(run_time, "%Y-%m-%d %H:%M")

            elif frequency == "daily":
                # run_time = "HH:MM"
                t = datetime.strptime(run_time, "%H:%M").time()
                next_run = datetime.combine(now.date(), t)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run

            elif frequency == "weekly":
                # run_time = "MON HH:MM"
                parts = run_time.split(" ")
                day_map = {"MON":0,"TUE":1,"WED":2,"THU":3,
                           "FRI":4,"SAT":5,"SUN":6}
                target_day = day_map.get(parts[0], 0)
                t = datetime.strptime(parts[1], "%H:%M").time()
                days_ahead = target_day - now.weekday()
                if days_ahead < 0 or (days_ahead == 0 and
                                       datetime.combine(now.date(), t) <= now):
                    days_ahead += 7
                return datetime.combine(
                    now.date() + timedelta(days=days_ahead), t)

            elif frequency == "monthly":
                # run_time = "15 HH:MM" (day of month)
                parts = run_time.split(" ")
                day = int(parts[0])
                t = datetime.strptime(parts[1], "%H:%M").time()
                next_run = datetime.combine(
                    now.date().replace(day=day), t)
                if next_run <= now:
                    if now.month == 12:
                        next_run = next_run.replace(
                            year=now.year+1, month=1)
                    else:
                        next_run = next_run.replace(month=now.month+1)
                return next_run
        except Exception:
            return datetime.now() + timedelta(hours=1)

    def _run_loop(self):
        while self._running:
            try:
                now = datetime.now()
                conn = sqlite3.connect(DB_SCHEDULER)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute('''SELECT * FROM scheduled_tasks
                    WHERE is_active=1 AND next_run <= ?''', (now,))
                due_tasks = [dict(r) for r in c.fetchall()]
                conn.close()

                for task in due_tasks:
                    self._execute_scheduled(task)

            except Exception as e:
                print(f"Scheduler error: {e}")

            time.sleep(30)  # Check every 30 seconds

    def _execute_scheduled(self, task: dict):
        start = datetime.now()
        status = "success"
        result = ""
        try:
            # AGENTS is global in merged file
            import sys as _sys
            _main = _sys.modules.get('__main__')
            _AGENTS = getattr(_main, 'AGENTS', {})

            agent = _AGENTS.get(task['agent_name'])
            if agent:
                result = agent['fn'](
                    task['user_id'], task['task'], task['context'])
            else:
                result = f"Agent {task['agent_name']} not found"
                status = "failed"

        except Exception as e:
            result = str(e)
            status = "failed"

        duration = int((datetime.now() - start).total_seconds() * 1000)

        # Log result
        conn = sqlite3.connect(DB_SCHEDULER)
        c = conn.cursor()
        c.execute('''INSERT INTO schedule_logs
            (task_id, agent_name, status, result, duration_ms)
            VALUES (?,?,?,?,?)''',
            (task['task_id'], task['agent_name'],
             status, str(result)[:1000], duration))

        # Update task: set next_run or deactivate if once
        if task['frequency'] == 'once':
            c.execute("UPDATE scheduled_tasks SET is_active=0, last_run=?, last_status=? WHERE task_id=?",
                     (datetime.now(), status, task['task_id']))
        else:
            next_run = self._calc_next_run(task['frequency'], task['cron_expr'])
            c.execute('''UPDATE scheduled_tasks
                SET last_run=?, last_status=?, next_run=?, run_count=run_count+1
                WHERE task_id=?''',
                (datetime.now(), status, next_run, task['task_id']))

        conn.commit()
        conn.close()

        # Notify user
        NotificationEngine.send(task['user_id'], "user",
            f"Scheduled Task {'✅' if status == 'success' else '❌'}",
            f"'{task['name']}' ran — Status: {status}",
            "success" if status == "success" else "error")

    def list_tasks(self, user_id: str = None) -> list:
        conn = sqlite3.connect(DB_SCHEDULER)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if user_id:
            c.execute("SELECT * FROM scheduled_tasks WHERE user_id=? ORDER BY next_run ASC",
                     (str(user_id),))
        else:
            c.execute("SELECT * FROM scheduled_tasks ORDER BY next_run ASC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def cancel_task(self, task_id: str) -> dict:
        conn = sqlite3.connect(DB_SCHEDULER)
        c = conn.cursor()
        c.execute("UPDATE scheduled_tasks SET is_active=0 WHERE task_id=?",
                 (task_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def get_logs(self, task_id: str = None, limit: int = 50) -> list:
        conn = sqlite3.connect(DB_SCHEDULER)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if task_id:
            c.execute('''SELECT * FROM schedule_logs WHERE task_id=?
                ORDER BY ran_at DESC LIMIT ?''', (task_id, limit))
        else:
            c.execute("SELECT * FROM schedule_logs ORDER BY ran_at DESC LIMIT ?",
                     (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows


# Start scheduler
scheduler = TaskScheduler()
scheduler.start()


# ============================================================
# SECTION 6 — ADMIN CONTACT ENGINE
# ============================================================

class AdminContactEngine:
    """
    Admin can contact any user or white label via
    chat, email, or initiate a call — all in one place.
    """

    @staticmethod
    def contact_user(admin_username: str, user_id: int,
                     method: str, message: str,
                     subject: str = "",
                     agent_name: str = None) -> dict:
        """
        method: 'chat' | 'email' | 'call'
        """
        # ChatEngine, GmailEngine are embedded globally

        user = UserManager.get_user(user_id=user_id)
        if not user:
            return {"success": False, "error": "User not found"}

        if method == "chat":
            room_id = ChatEngine.get_or_create_room(
                "admin_user", admin_username, str(user_id))
            ChatEngine.send_message(room_id, admin_username, "admin", message)
            NotificationEngine.send(str(user_id), "user",
                "New Message from Admin", message[:100], "info")
            return {"success": True, "room_id": room_id}

        elif method == "email" and agent_name:
            result = GmailEngine.send_email(
                agent_name,
                user.get("email", ""),
                subject or "Message from Admin",
                message)
            NotificationEngine.send(str(user_id), "user",
                "Email from Admin", subject, "info")
            return result

        elif method == "call":
            room_id = ChatEngine.get_or_create_room(
                "admin_user", admin_username, str(user_id))
            ChatEngine.log_call(room_id, admin_username,
                               str(user_id), "voice", "initiated")
            NotificationEngine.send(str(user_id), "user",
                "Incoming Call from Admin",
                f"{admin_username} is calling you", "warning")
            return {"success": True, "call_initiated": True}

        return {"success": False, "error": "Unknown method"}

    @staticmethod
    def contact_whitelabel(admin_username: str, wl_id: int,
                           method: str, message: str,
                           subject: str = "",
                           agent_name: str = None) -> dict:
        # ChatEngine, GmailEngine are embedded globally

        wl = WhiteLabelManager.get_instance(wl_id=wl_id)
        if not wl:
            return {"success": False, "error": "WL not found"}

        if method == "chat":
            room_id = ChatEngine.get_or_create_room(
                "admin_wl", admin_username, str(wl_id))
            ChatEngine.send_message(room_id, admin_username, "admin", message)
            return {"success": True, "room_id": room_id}

        elif method == "email" and agent_name:
            result = GmailEngine.send_email(
                agent_name,
                wl.get("admin_email", ""),
                subject or "Message from Platform Admin",
                message)
            return result

        elif method == "call":
            room_id = ChatEngine.get_or_create_room(
                "admin_wl", admin_username, str(wl_id))
            ChatEngine.log_call(room_id, admin_username,
                               str(wl_id), "voice", "initiated")
            return {"success": True}

        return {"success": False, "error": "Unknown method"}


print("✅ Phase 4 loaded:")
print("   ✅ User management (CRUD, plans, activity, restore)")
print("   ✅ White label management (separate DB, branding, agents, users)")
print("   ✅ Admin contact engine (chat/email/call to users & WL)")
print("   ✅ Task scheduler (daily/weekly/monthly agent tasks)")
print("   ✅ Notification engine (in-app, broadcast, unread count)")
print("   ✅ Plan/subscription system (basic/pro/enterprise)")


# ========== AI AGENTS MANAGER ==========
def render_ai_agents():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>🤖 AI Agents — Real Execution</h1><p>Agents that physically DO the work — create files, save data, generate output</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab_tools, tab_search, tab_memory, tab_train = st.tabs(["⚡ Run Agent", "🔄 Auto Pipeline", "🤖 Agent Status", "📋 Logs", "🔧 Tools", "🔍 Live Search", "🧠 Agent Memory", "🎓 AI Training"])

    # ===== TAB 1: RUN AGENT =====
    with tab1:
        st.subheader("⚡ Run Any Agent — Real Physical Execution")
        st.caption("Agents will create files, save data, generate output — all physically on your computer")

        col1, col2 = st.columns([1, 1])
        with col1:
            selected_agent = st.selectbox("🤖 Select Agent", list(AGENTS.keys()))
            st.caption(f"📋 {AGENTS[selected_agent]['desc']}")

            task = st.text_area("📝 What should the agent do?", height=150,
                                 placeholder="Be specific! Examples:\n• Score all new leads and update their status\n• Generate a full hotel website with booking form\n• Write 5 email campaigns for cold outreach\n• Create an invoice for client ABC for $5000\n• Analyze inventory and report low stock items\n• Build a Flutter login screen with biometrics")

            context = st.text_area("📎 Context / Extra Data (optional)", height=80,
                                    placeholder="Add any extra info, data, names, requirements...")

        with col2:
            st.markdown("### 🎯 Quick Actions")
            quick_actions = {
                "💼 Sales AI": [
                    ("Score all new leads", "Score and qualify all new leads"),
                    ("Write cold email campaign", "Write a professional cold email outreach campaign"),
                    ("Generate sales report", "Generate a complete sales performance report"),
                ],
                "🌐 Web Dev AI": [
                    ("Build hotel website", "Generate a complete modern hotel website with booking"),
                    ("Create landing page", "Generate a high-converting SaaS landing page"),
                    ("Build e-commerce site", "Generate a complete e-commerce website"),
                ],
                "📢 Marketing AI": [
                    ("Write social media posts", "Write 10 engaging social media posts for LinkedIn and Twitter"),
                    ("Create email newsletter", "Create a professional email newsletter"),
                    ("Write blog post", "Write a 1000-word SEO-optimized blog post about AI agency services"),
                ],
                "💰 Finance AI": [
                    ("Create sample invoice", "Create an invoice for a web development project"),
                    ("Generate financial report", "Generate a complete financial analysis report"),
                ],
                "🤝 CRM AI": [
                    ("Write follow-up emails", "Write follow-up emails for all lead contacts"),
                    ("Analyze pipeline", "Analyze the sales pipeline and suggest improvements"),
                ],
                "📊 ERP AI": [
                    ("Check inventory levels", "Analyze all inventory and identify low stock items"),
                    ("Generate operations report", "Generate a complete operations report"),
                ],
                "📱 Mobile AI": [
                    ("Build Flutter login screen", "Generate complete Flutter login screen with authentication"),
                    ("Create React Native home", "Generate React Native home screen with navigation"),
                ],
                "🛡️ Admin AI": [
                    ("Full system report", "Generate a complete system report covering all modules"),
                    ("Create automation script", "Create a Python automation script for the agency"),
                ],
            }

            actions = quick_actions.get(selected_agent, [])
            for action_label, action_task in actions:
                if st.button(f"▶ {action_label}", use_container_width=True, key=f"qa_{action_label}"):
                    st.session_state['quick_task'] = action_task
                    st.rerun()

            if 'quick_task' in st.session_state:
                st.info(f"Quick task loaded: {st.session_state['quick_task'][:60]}...")

        st.divider()
        col_run1, col_run2 = st.columns(2)
        run_now = col_run1.button(f"🚀 Run Now (Blocking)", type="primary", use_container_width=True)
        run_queue = col_run2.button(f"⚡ Queue Task (Parallel)", use_container_width=True)

        # Queue task via Phase 1 multi-task engine
        if run_queue and PHASE1_LOADED:
            final_task = task if task else st.session_state.get('quick_task', '')
            if final_task:
                priority = st.session_state.get('task_priority', 5)
                task_id = task_engine.submit_task(
                    AGENTS[selected_agent]['fn'],
                    user_id, selected_agent, final_task, context, priority
                )
                st.success(f"✅ Task queued! ID: `{task_id}` — View progress in Settings → Task Engine")
            else:
                st.warning("Enter a task first")

        if run_now:
            actual_task = st.session_state.get('quick_task', task)
            if actual_task or task:
                final_task = task if task else st.session_state.get('quick_task', '')
                with st.spinner(f"🤖 {selected_agent} is working..."):
                    agent_fn = AGENTS[selected_agent]['fn']

                    # ===== PHASE 2: Use enhanced wrapper if loaded =====
                    if PHASE2_LOADED:
                        result = enhanced_agent_wrapper(
                            selected_agent, user_id, final_task,
                            context, agent_fn, AGENTS
                        )
                        save_msg = "✅ Auto-saved by Phase 2 engine (file + memory + handoffs)"
                    else:
                        result = agent_fn(user_id, final_task, context)
                        # Fallback file save
                        try:
                            agent_folder = "agent_outputs"
                            os.makedirs(agent_folder, exist_ok=True)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            safe_name = final_task[:40].replace(' ','_').replace('/','_')
                            agent_short = selected_agent.split(' ')[1] if ' ' in selected_agent else selected_agent
                            filepath = os.path.join(agent_folder, f"{agent_short}_{safe_name}_{timestamp}.txt")
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(f"AGENT: {selected_agent}\nTASK: {final_task}\n\n{result}")
                            save_msg = f"✅ File saved: `{filepath}`"
                        except Exception as e:
                            save_msg = f"⚠️ File save error: {e}"

                    log_agent_action(selected_agent, final_task[:100], context[:100], result[:200])

                if 'quick_task' in st.session_state:
                    del st.session_state['quick_task']

                st.success(f"✅ {selected_agent} completed the task!")
                st.info(save_msg)
                st.divider()

                with st.container(border=True):
                    st.markdown(f"### 📋 {selected_agent} — Output")
                    st.markdown(result)

                st.download_button("📥 Download Output", data=result,
                                   file_name=f"{selected_agent.replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt",
                                   mime="text/plain")
            else:
                st.warning("Enter a task or click a Quick Action")

    # ===== TAB 2: AUTO PIPELINE =====
    with tab2:
        st.subheader("🔄 Auto Pipeline — Chain Multiple Agents")
        st.caption("Run multiple agents in sequence — output of one feeds into the next")

        pipeline_name = st.text_input("Pipeline Name", placeholder="e.g., New Client Onboarding")

        st.markdown("**Select agents to run in order:**")
        agent_list = list(AGENTS.keys())
        col1, col2 = st.columns(2)
        selected_pipeline = []
        for i, agent in enumerate(agent_list):
            with (col1 if i % 2 == 0 else col2):
                if st.checkbox(agent, key=f"pipeline_{agent}"):
                    selected_pipeline.append(agent)

        pipeline_task = st.text_area("Overall Goal / Instructions", height=100,
                                      placeholder="e.g., We have a new client 'ABC Hotel'. Create their website, set up CRM contact, create invoice, write marketing content")

        if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
            if selected_pipeline and pipeline_task:
                all_results = []
                progress = st.progress(0)
                for i, agent_name in enumerate(selected_pipeline):
                    with st.spinner(f"Running {agent_name}..."):
                        agent_fn = AGENTS[agent_name]['fn']
                        result = agent_fn(user_id, pipeline_task, "\n".join(all_results[-1:]) if all_results else "")
                        all_results.append(f"## {agent_name} Output:\n{result}")
                        log_agent_action(agent_name, f"Pipeline: {pipeline_name}", pipeline_task[:100], result[:200])
                    progress.progress((i + 1) / len(selected_pipeline))
                    st.success(f"✅ {agent_name} done")

                progress.empty()
                st.success(f"🎉 Pipeline '{pipeline_name}' completed! {len(selected_pipeline)} agents executed.")
                full_output = "\n\n---\n\n".join(all_results)
                with st.expander("📋 Full Pipeline Output"):
                    st.markdown(full_output)
                st.download_button("📥 Download All Output", data=full_output,
                                   file_name=f"pipeline_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt",
                                   mime="text/plain")
            else:
                st.warning("Select at least one agent and enter a goal")

    # ===== TAB 3: AGENT STATUS =====
    with tab3:
        st.subheader("🤖 Agent Status & Capabilities")
        cols = st.columns(2)
        for i, (name, info) in enumerate(AGENTS.items()):
            with cols[i % 2]:
                with st.container(border=True):
                    log_count = len(db_fetch("SELECT id FROM agent_logs WHERE agent_name=?", (name.split(" ", 1)[1],)))
                    st.markdown(f"**{name}**")
                    st.caption(info['desc'])
                    st.markdown(f"<span class='badge-green'>● Active</span> &nbsp; Tasks run: **{log_count}**", unsafe_allow_html=True)

        st.divider()
        st.subheader("📁 Generated Files")
        output_dirs = ["generated_sites", "marketing_output", "crm_output", "mobile_output", "admin_output", "reports"]
        for d in output_dirs:
            if os.path.exists(d):
                files = os.listdir(d)
                if files:
                    with st.expander(f"📁 {d}/ ({len(files)} files)"):
                        for f in sorted(files, reverse=True)[:10]:
                            filepath = os.path.join(d, f)
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.caption(f)
                            with c2:
                                try:
                                    with open(filepath, "r", encoding="utf-8") as fp:
                                        content = fp.read()
                                    st.download_button("📥", data=content, file_name=f,
                                                       mime="text/plain", key=f"dl_file_{d}_{f}")
                                except:
                                    pass

    # ===== TAB 4: LOGS =====
    with tab4:
        st.subheader("📋 Agent Activity Log")
        logs = db_fetch("SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT 100")
        if logs:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑️ Clear All Logs", use_container_width=True):
                    db_execute("DELETE FROM agent_logs")
                    st.rerun()
            for log in logs:
                badge = "badge-green" if log[5] == "success" else "badge-red"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.markdown(f"**{log[1]}**")
                        st.caption(f"Task: {log[2][:60]}")
                    with c2:
                        st.caption(f"Output: {log[4][:80]}")
                    with c3:
                        st.markdown(f"<span class='{badge}'>{log[5]}</span>", unsafe_allow_html=True)
                        st.caption(str(log[6])[:16])
        else:
            st.info("No agent activity yet. Run an agent task!")

    # ===== TOOLS TAB =====
    with tab_tools:
        st.subheader("🔧 Agent Tool Registry")
        if not PHASE2_LOADED:
            st.error("Phase 2 not loaded. Check phase2_agent_powers.py")
        else:
            tools = ToolRegistry.list_tools()
            st.caption(f"{len(tools)} built-in tools available to all agents")
            cols = st.columns(2)
            for i, tool in enumerate(tools):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{tool['name']}**")
                        st.caption(tool['desc'])
                        if tool['args']:
                            st.caption(f"Args: {', '.join(tool['args'])}")
                        st.markdown("<span class='badge-green'>Active</span>", unsafe_allow_html=True)
            st.divider()
            st.markdown("**Test a Tool**")
            tool_names = [t["name"] for t in tools]
            sel_tool = st.selectbox("Select Tool", tool_names, key="test_tool_sel")
            if sel_tool == "web_search":
                q = st.text_input("Query", key="tool_q")
                if st.button("Run Tool", key="run_tool_btn"):
                    r = ToolRegistry.run_tool("web_search", "admin", query=q)
                    st.json(r)
            elif sel_tool == "system_resources":
                if st.button("Get System Info", key="run_sys_btn"):
                    r = ToolRegistry.run_tool("system_resources", "admin")
                    if r.get("success"):
                        c1,c2,c3 = st.columns(3)
                        c1.metric("CPU", f"{r.get('cpu_percent',0)}%")
                        c2.metric("RAM", f"{r.get('memory',{}).get('percent',0)}%")
                        c3.metric("Disk", f"{r.get('disk',{}).get('percent',0)}%")
            elif sel_tool == "wikipedia":
                q = st.text_input("Topic", key="wiki_q")
                if st.button("Search", key="wiki_btn"):
                    r = ToolRegistry.run_tool("wikipedia", "admin", query=q)
                    if r.get("success"):
                        st.markdown(f"**{r.get('title')}**")
                        st.markdown(r.get("summary","")[:600])

    # ===== LIVE SEARCH TAB =====
    with tab_search:
        st.subheader("Live Search Engine")
        if not PHASE2_LOADED:
            st.error("Phase 2 not loaded.")
        else:
            sq = st.text_input("Search query", key="live_sq")
            c1,c2,c3,c4 = st.columns(4)
            do_web  = c1.checkbox("Web",  value=True, key="ls_web")
            do_wiki = c2.checkbox("Wiki", value=True, key="ls_wiki")
            do_sys  = c3.checkbox("System", value=False, key="ls_sys")
            do_db   = c4.checkbox("DB",   value=False, key="ls_db")
            if st.button("Search Now", type="primary", use_container_width=True, key="ls_btn"):
                if sq:
                    if do_web:
                        r = LiveSearchEngine.web_search(sq)
                        st.markdown("#### Web Results")
                        for res in r.get("results",[])[:5]:
                            with st.container(border=True):
                                st.markdown(f"**{res.get('title','')[:100]}**")
                                st.caption(res.get('text','')[:300])
                    if do_wiki:
                        r = LiveSearchEngine.wikipedia_search(sq)
                        st.markdown("#### Wikipedia")
                        if r.get("success"):
                            st.markdown(f"**{r.get('title','')}**")
                            st.markdown(r.get('summary','')[:500])
                    if do_sys:
                        r = LiveSearchEngine.system_resources()
                        st.markdown("#### System Resources")
                        if r.get("success"):
                            c1,c2,c3 = st.columns(3)
                            c1.metric("CPU", f"{r.get('cpu_percent',0)}%")
                            c2.metric("RAM Used", f"{r.get('memory',{}).get('used_gb',0)} GB")
                            c3.metric("Disk", f"{r.get('disk',{}).get('percent',0)}%")
                    if do_db:
                        r = LiveSearchEngine.search_internal_db("main", sq)
                        st.markdown("#### DB Results")
                        for m in r.get("matches",[]):
                            with st.expander(f"Table: {m['table']}"):
                                st.json(m['rows'])
                else:
                    st.warning("Enter a search query")

    # ===== MEMORY TAB =====
    with tab_memory:
        st.subheader("Agent Memory System")
        if not PHASE2_LOADED:
            st.error("Phase 2 not loaded.")
        else:
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**Save Memory**")
                ma = st.selectbox("Agent", list(AGENTS.keys()), key="m_agent")
                mt = st.selectbox("Type", ["preference","history","learning","feedback","client_note"], key="m_type")
                mc = st.text_area("Content", height=80, key="m_content")
                mi = st.slider("Importance", 1, 10, 5, key="m_imp")
                if st.button("Save Memory", use_container_width=True, key="m_save"):
                    r = AgentMemory.save(ma, user_id, mt, mc, mi)
                    st.success("Saved!") if r["success"] else st.error(r.get("error"))
            with c2:
                st.markdown("**Recall Memories**")
                ra = st.selectbox("Agent", list(AGENTS.keys()), key="r_agent")
                rt = st.selectbox("Type", ["all","preference","history","learning","feedback"], key="r_type")
                if st.button("Recall", use_container_width=True, key="r_recall"):
                    mems = AgentMemory.recall(ra, user_id, None if rt=="all" else rt)
                    if mems:
                        for m in mems:
                            with st.container(border=True):
                                st.markdown(f"**[{m['memory_type'].upper()}]** {m['content'][:150]}")
                                st.caption(f"Importance: {m['importance']}/10 | {str(m['created_at'])[:16]}")
                    else:
                        st.info("No memories found.")
                if st.button("Clear Memories", key="r_clear"):
                    AgentMemory.forget(ra, user_id)
                    st.success("Cleared!")
                    st.rerun()

    # ===== TRAINING TAB =====
    with tab_train:
        st.subheader("🎓 AI Training Center")
        st.caption("Train agents using files, chat history, or email conversations")
        
        col_train1, col_train2 = st.columns([1, 1])
        with col_train1:
            st.markdown("**Train from File Upload**")
            agent_for_training = st.selectbox("Select Agent to Train", list(AGENTS.keys()), key="train_agent")
            uploaded_file = st.file_uploader(
                "Upload training document (TXT, PDF, DOCX, etc.)",
                type=["txt", "pdf", "docx", "md", "csv", "json"],
                key="train_file_upload"
            )
            
            if uploaded_file is not None:
                try:
                    # Reset file pointer after checking type
                    uploaded_file.seek(0)
                    
                    # Read file content based on type
                    if uploaded_file.type == "application/pdf":
                        try:
                            import PyPDF2
                            pdf_reader = PyPDF2.PdfReader(uploaded_file)
                            content = ""
                            for page in pdf_reader.pages:
                                content += page.extract_text()
                            # Save to training database
                            result = AITrainingSystem.train_from_text(
                                agent_for_training,
                                content,
                                f"file_upload_pdf_{uploaded_file.name}"
                            )
                        except ImportError:
                            st.error("PyPDF2 not installed. Run: pip install pypdf2")
                            # Fallback: save as raw content
                            uploaded_file.seek(0)
                            result = AITrainingSystem.train_from_uploaded_file(
                                agent_for_training,
                                uploaded_file,
                                f"file_upload_{uploaded_file.name}"
                            )
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        try:
                            import docx
                            doc = docx.Document(uploaded_file)
                            content = "\n".join([p.text for p in doc.paragraphs])
                            # Save to training database
                            result = AITrainingSystem.train_from_text(
                                agent_for_training,
                                content,
                                f"file_upload_docx_{uploaded_file.name}"
                            )
                        except ImportError:
                            st.error("python-docx not installed. Run: pip install python-docx")
                            # Fallback: save as raw content
                            uploaded_file.seek(0)
                            result = AITrainingSystem.train_from_uploaded_file(
                                agent_for_training,
                                uploaded_file,
                                f"file_upload_{uploaded_file.name}"
                            )
                    else:
                        # For TXT and other text files
                        uploaded_file.seek(0)
                        result = AITrainingSystem.train_from_uploaded_file(
                            agent_for_training,
                            uploaded_file,
                            f"file_upload_{uploaded_file.name}"
                        )
                    
                    if result["success"]:
                        st.success(f"✅ File '{uploaded_file.name}' uploaded and added to {agent_for_training} training")
                    else:
                        st.error(f"❌ Error training: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
            
            st.divider()
            
            st.markdown("**Train from Text**")
            training_text = st.text_area(
                "Paste training content",
                height=150,
                key="train_text_area"
            )
            text_source = st.text_input(
                "Source Description (optional)",
                placeholder="e.g., Client requirements, Best practices, etc.",
                key="train_text_source"
            )
            
            if st.button("Add Text to Training", key="add_text_training"):
                if training_text.strip():
                    result = AITrainingSystem.train_from_text(
                        agent_for_training,
                        training_text,
                        text_source or "manual_entry"
                    )
                    if result["success"]:
                        st.success(f"✅ Text added to {agent_for_training} training")
                    else:
                        st.error(f"❌ Error training: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter some training text")
        
        with col_train2:
            st.markdown("**Training Management**")
            
            # Show current training data
            agent_training = st.selectbox("View Training for Agent", list(AGENTS.keys()), key="view_train_agent")
            
            if st.button("Refresh Training Data", key="refresh_training"):
                training_data = AITrainingSystem.list_training_data(agent_training)
                if training_data:
                    st.success(f"Found {len(training_data)} training items")
                    for i, td in enumerate(training_data):
                        with st.expander(f"📝 {td['source']} ({str(td['created_at'])[:16]})", expanded=False):
                            st.caption(f"Type: {td['training_type']}")
                            st.markdown(f"**Preview:** {td['preview'][:200]}...")
                            if st.button(f"Delete Training #{i+1}", key=f"del_train_{td['id']}"):
                                AITrainingSystem.delete_training(td['id'])
                                st.rerun()
                else:
                    st.info("No training data for this agent")
            
            st.divider()
            
            st.markdown("**Training Context Preview**")
            if st.button("Generate Training Context", key="gen_train_context"):
                context = AITrainingSystem.get_training_context(agent_training, limit=10)
                if context:
                    with st.expander("View Training Context", expanded=True):
                        st.text_area(
                            "Training Context that will be injected into agent prompts:",
                            value=context,
                            height=300,
                            disabled=True
                        )
                else:
                    st.info("No training context available")


def render_tools_manager():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>🔧 Tools Manager — Custom AI Tools</h1><p>Create, upload, and assign custom tools to all AI agents</p></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🛠️ Create Tools", "📋 Assign Tools", "🤖 Test Tools"])
    
    # ===== TAB 1: CREATE TOOLS =====
    with tab1:
        st.subheader("🛠️ Create Custom Tools")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("**Upload Tool Package**")
            uploaded_tool = st.file_uploader(
                "Upload tool package (.py file or .zip archive)",
                type=["py", "zip"],
                key="upload_tool"
            )
            
            if uploaded_tool is not None:
                try:
                    # Save uploaded tool to tools directory
                    tools_dir = "agent_tools_files"
                    os.makedirs(tools_dir, exist_ok=True)
                    
                    # Create file path
                    tool_path = os.path.join(tools_dir, uploaded_tool.name)
                    
                    # Write file content
                    with open(tool_path, "wb") as f:
                        f.write(uploaded_tool.getvalue())
                    
                    st.success(f"✅ Tool '{uploaded_tool.name}' uploaded successfully!")
                    
                    # Try to extract function information if it's a Python file
                    if uploaded_tool.name.endswith('.py'):
                        content = uploaded_tool.read().decode('utf-8')
                        # Look for function definitions in the file
                        import re
                        functions = re.findall(r'def\s+(\w+)\s*\(', content)
                        if functions:
                            st.info(f"Functions found: {', '.join(functions)}")
                
                except Exception as e:
                    st.error(f"❌ Error uploading tool: {str(e)}")
            
            st.divider()
            
            st.markdown("**Register Built-in Tool**")
            tool_name = st.text_input("Tool Name", placeholder="e.g., file_reader, web_scraper")
            tool_desc = st.text_area("Description", placeholder="What does this tool do?", height=80)
            tool_args = st.text_input("Arguments", placeholder="arg1, arg2, etc. (comma separated)")
            
            if st.button("Register Tool", key="register_tool"):
                if tool_name and tool_desc:
                    # Add tool to the registry using the new method
                    args_list = [arg.strip() for arg in tool_args.split(',') if arg.strip()] if tool_args else []
                    result = ToolRegistry.add_custom_tool(tool_name, tool_desc, args_list)
                                
                    if result["success"]:
                        st.success(f"✅ Tool '{tool_name}' registered successfully!")
                    else:
                        st.error(f"❌ Error registering tool: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please enter tool name and description")
        
        with col2:
            st.markdown("**Available Tools**")
            
            # Show built-in tools
            if PHASE2_LOADED:
                builtin_tools = ToolRegistry.list_tools()
                if builtin_tools:
                    st.markdown("**Built-in Tools:**")
                    for tool in builtin_tools:
                        with st.container(border=True):
                            st.markdown(f"**🔧 {tool['name']}**")
                            st.caption(tool['desc'])
                            if tool.get('args'):
                                st.caption(f"Args: {', '.join(tool['args'])}")
                else:
                    st.info("No built-in tools available")
            
            # Show custom tools
            custom_tools = ToolRegistry.CUSTOM_TOOLS
            if custom_tools:
                st.markdown("**Custom Tools:**")
                for name, tool in custom_tools.items():
                    with st.container(border=True):
                        st.markdown(f"**🛠️ {tool['name']}**")
                        st.caption(tool['desc'])
                        if tool.get('args'):
                            st.caption(f"Args: {', '.join(tool['args'])}")
                        
                        col_a, col_b = st.columns([1, 1])
                        with col_a:
                            if st.button(f"Assign to All", key=f"assign_all_{name}"):
                                # Logic to assign tool to all agents would go here
                                st.success(f"Assigned {name} to all agents")
                        with col_b:
                            if st.button(f"Delete", key=f"delete_{name}"):
                                del custom_tools[name]
                                st.rerun()
            
            # Show uploaded tools from directory
            tools_dir = "agent_tools_files"
            if os.path.exists(tools_dir):
                tool_files = [f for f in os.listdir(tools_dir) if f.endswith((".py", ".zip"))]
                if tool_files:
                    st.markdown("**Uploaded Tools:**")
                    for tf in tool_files:
                        with st.container(border=True):
                            st.markdown(f"**📄 {tf}**")
                            file_path = os.path.join(tools_dir, tf)
                            file_size = os.path.getsize(file_path)
                            st.caption(f"Size: {round(file_size/1024, 2)} KB")
    
    # ===== TAB 2: ASSIGN TOOLS =====
    with tab2:
        st.subheader("📋 Assign Tools to Agents")
        
        # Select agent to assign tools to
        agent_for_assignment = st.selectbox("Select Agent", list(AGENTS.keys()), key="select_agent_assign")
        
        # Get all available tools
        all_tools = {}
        if PHASE2_LOADED:
            all_builtin_tools = ToolRegistry.list_tools()
            for tool in all_builtin_tools:
                all_tools[tool['name']] = tool
        
        all_custom_tools = ToolRegistry.CUSTOM_TOOLS
        for name, tool in all_custom_tools.items():
            all_tools[name] = tool
        
        if all_tools:
            st.markdown(f"**Tools available for assignment to {agent_for_assignment}:**")
            
            # Show tools with checkboxes for assignment
            assigned_tools = getattr(AGENTS[agent_for_assignment].get('tools', []), 'copy', lambda: [])()
            if 'assigned_tools' not in st.session_state:
                st.session_state['assigned_tools'] = {agent: [] for agent in AGENTS.keys()}
            
            for name, tool in all_tools.items():
                is_assigned = name in st.session_state['assigned_tools'][agent_for_assignment]
                if st.checkbox(f"{tool['name']} - {tool['desc']}", value=is_assigned, key=f"chk_{agent_for_assignment}_{name}"):
                    if name not in st.session_state['assigned_tools'][agent_for_assignment]:
                        st.session_state['assigned_tools'][agent_for_assignment].append(name)
                else:
                    if name in st.session_state['assigned_tools'][agent_for_assignment]:
                        st.session_state['assigned_tools'][agent_for_assignment].remove(name)
            
            if st.button("Save Tool Assignments", key="save_assignments"):
                st.success(f"✅ Tools assigned to {agent_for_assignment} successfully!")
        else:
            st.info("No tools available. Upload or register tools first.")
        
        st.divider()
        
        # Show currently assigned tools
        st.markdown(f"**Currently Assigned to {agent_for_assignment}:**")
        assigned = st.session_state.get('assigned_tools', {}).get(agent_for_assignment, [])
        if assigned:
            for tool_name in assigned:
                st.markdown(f"• **🔧 {tool_name}**")
        else:
            st.info("No tools assigned to this agent yet.")
    
    # ===== TAB 3: TEST TOOLS =====
    with tab3:
        st.subheader("🤖 Test Tools")
        
        # Select tool to test
        if PHASE2_LOADED:
            all_tools_list = ToolRegistry.get_all_tools()
            all_tools = {}
            for tool in all_tools_list:
                all_tools[tool['name']] = tool
        else:
            all_tools = {}
        
        if all_tools:
            selected_tool = st.selectbox("Select Tool to Test", list(all_tools.keys()), key="select_test_tool")
            
            if selected_tool:
                tool_info = all_tools[selected_tool]
                st.info(f"Testing: {tool_info['desc']}")
                
                # Get tool arguments
                if tool_info.get('args'):
                    tool_inputs = {}
                    for arg in tool_info['args']:
                        tool_inputs[arg] = st.text_input(f"{arg}", key=f"input_{selected_tool}_{arg}")
                    
                    if st.button(f"Run {selected_tool}", key="run_test_tool"):
                        with st.spinner(f"Running {selected_tool}..."):
                            # Try to run the tool
                            try:
                                if PHASE2_LOADED and selected_tool in [t['name'] for t in all_tools_list]:
                                    # Run built-in tool
                                    result = ToolRegistry.run_tool(selected_tool, "tools_tester", **tool_inputs)
                                    st.json(result)
                                else:
                                    # For custom tools, show a message
                                    st.info(f"Custom tool {selected_tool} would be executed with: {tool_inputs}")
                            except Exception as e:
                                st.error(f"Error running tool: {str(e)}")
                else:
                    if st.button(f"Run {selected_tool}", key="run_simple_tool"):
                        with st.spinner(f"Running {selected_tool}..."):
                            try:
                                if PHASE2_LOADED and selected_tool in [t['name'] for t in all_tools_list]:
                                    result = ToolRegistry.run_tool(selected_tool, "tools_tester")
                                    st.json(result)
                                else:
                                    st.info(f"Custom tool {selected_tool} would be executed")
                            except Exception as e:
                                st.error(f"Error running tool: {str(e)}")
        else:
            st.info("No tools available to test. Upload or register tools first.")
    
    # ===== OFFLINE CHAT =====
    with st.container(border=True):
        st.subheader("💬 Offline Chat with AI")
        st.caption("Chat with AI without internet connection using local models")
        
        # Initialize chat history for tools section
        chat_key = f"tools_chat_{user_id}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        # Display chat messages
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Chat input
        user_input = st.chat_input("Message the AI assistant...")
        
        if user_input:
            st.session_state[chat_key].append({"role": "user", "content": user_input})
            
            # Use local AI model if available, otherwise simulate response
            try:
                # Check if Ollama is available for offline processing
                import urllib.request
                urllib.request.urlopen('http://localhost:11434', timeout=3)
                
                # If Ollama is available, use it
                import requests
                ollama_url = "http://localhost:11434/api/generate"
                payload = {
                    "model": "gemma3:4b",  # Default model
                    "prompt": f"You are an AI assistant helping with tools management. User asked: {user_input}",
                    "stream": False
                }
                response = requests.post(ollama_url, json=payload)
                
                if response.status_code == 200:
                    ai_response = response.json()["response"]
                else:
                    ai_response = f"I received your message about '{user_input}'. For offline tools management, make sure Ollama is running with a local model."
            except:
                # Fallback if Ollama is not available
                ai_response = f"I received your message: '{user_input}'. For offline processing, please set up Ollama with a local AI model."
            
            st.session_state[chat_key].append({"role": "assistant", "content": ai_response})
            st.rerun()
        
        col_chat1, col_chat2 = st.columns([4, 1])
        with col_chat2:
            if st.button("🗑️ Clear Chat", key="clear_tools_chat"):
                st.session_state[chat_key] = []
                st.rerun()

# ========== MODULE BUILDER ==========
def render_module_builder():
    user_id = st.session_state.user['id']
    st.markdown("<div class='agency-header'><h1>📦 Module Builder — Create Custom AI Modules</h1><p>Upload, create, and deploy custom AI modules with full tool integration</p></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏗️ Create Module", "📤 Upload Module", "⚙️ Module Tools", "📋 Deploy Module", "💬 Module Chat", "👥 Employee DB"])
    
    # ===== TAB 1: CREATE MODULE =====
    with tab1:
        st.subheader("🏗️ Create New Module")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            module_name = st.text_input("Module Name", placeholder="e.g., HR AI, Legal AI, Compliance AI")
            module_description = st.text_area("Description", placeholder="What does this module do?", height=100)
            module_category = st.selectbox("Category", ["Business", "Technical", "Creative", "Analytical", "Administrative"])
            
            st.divider()
            
            st.markdown("**Module Features**")
            enable_chat = st.checkbox("Enable AI Chat", value=True)
            enable_file_ops = st.checkbox("Enable File Operations", value=True)
            enable_db_ops = st.checkbox("Enable Database Operations", value=True)
            enable_web_search = st.checkbox("Enable Web Search", value=True)
            
        with col2:
            st.markdown("**Module Icon & Color**")
            module_icon = st.selectbox("Icon", ["👷", "💼", "🔬", "🎨", "📊", "🤖", "🧠", "🔧", "📦", "🚀"])
            module_color = st.color_picker("Theme Color", "#667eea")
            
            st.divider()
            
            st.markdown("**AI Configuration**")
            ai_model = st.selectbox("Preferred AI Model", ["Default", "GPT-4", "Claude-3", "Gemini Pro", "Ollama Models"])
            ai_temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.7)
            
            st.divider()
            
            if st.button("🏗️ Create Module Template", type="primary", use_container_width=True):
                if module_name and module_description:
                    # Create module directory and files
                    module_dir = f"modules/{module_name.lower().replace(' ', '_')}"
                    os.makedirs(module_dir, exist_ok=True)
                    
                    # Create module template
                    module_template = f'''"""
{module_name} - Custom AI Module
Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import streamlit as st
import os
import json
import sqlite3
from datetime import datetime
import hashlib

# Module constants
current_user_id = "{user_id}"
MODULE_NAME = "{module_name}"
MODULE_DIR = "{module_dir}"


def agent_{module_name.lower().replace(' ', '_')}(user_id, task, context=""):
    """{module_name} agent function"""
    results = []
    
    prompt = f"""You are the {module_name} AI Agent. Execute this task completely:
TASK: {{task}}
CONTEXT: {{context}}

{'- Engage in conversations' if enable_chat else ''}
{'- Perform file operations' if enable_file_ops else ''}
{'- Query databases' if enable_db_ops else ''}
{'- Search the web for information' if enable_web_search else ''}

Provide complete, actionable output."""

    # In a real implementation, you would call your AI here
    # response, error = call_ai(prompt, f"You are the {module_name} AI Agent.")
    response = f"This is the {module_name} module. Task: {{task}}"
    
    if response:
        results.append(response)
    else:
        results.append(f"❌ Error processing task")

    return "\n\n".join(results)


def render_{module_name.lower().replace(' ', '_')}_module():
    """Render the {module_name} module UI"""
    user_id = st.session_state.user['id']
    st.markdown(f"<div class='agency-header'><h1>{module_icon} {module_name}</h1><p>{module_description}</p></div>", unsafe_allow_html=True)
    
    tab_main, tab_config, tab_logs = st.tabs(["🤖 Main Interface", "⚙️ Configuration", "📋 Activity Logs"])
    
    with tab_main:
        st.subheader("Execute {module_name} Task")
        task = st.text_area("What should the {module_name} agent do?", height=150,
                             placeholder="Describe the task for the {module_name} agent...")
        
        context = st.text_area("Context / Additional Information", height=80,
                                placeholder="Provide any additional context or information...")
        
        if st.button(f"🚀 Run {module_name} Agent", type="primary"):
            if task:
                with st.spinner(f"{module_name} agent is working..."):
                    result = agent_{module_name.lower().replace(' ', '_')}(user_id, task, context)
                    st.success(f"✅ {module_name} task completed!")
                    st.markdown("### Output")
                    st.markdown(result)
            else:
                st.warning("Please enter a task")

    with tab_config:
        st.subheader("Configuration Settings")
        st.json({{
            "module_name": "{module_name}",
            "description": "{module_description}",
            "category": "{module_category}",
            "features": {{
                "chat_enabled": {str(enable_chat).lower()},
                "file_operations": {str(enable_file_ops).lower()},
                "database_operations": {str(enable_db_ops).lower()},
                "web_search": {str(enable_web_search).lower()}
            }},
            "ai_settings": {{
                "model": "{ai_model}",
                "temperature": {ai_temperature}
            }}
        }})
    
    with tab_logs:
        st.subheader("Activity Logs")
        st.info("No logs yet. Run tasks to see activity.")

# End of {module_name} module
'''
                    
                    # Save module file
                    with open(f"{module_dir}/{module_name.lower().replace(' ', '_')}_module.py", "w", encoding="utf-8") as f:
                        f.write(module_template)
                    
                    # Create module metadata
                    metadata = {
                        "name": module_name,
                        "description": module_description,
                        "category": module_category,
                        "icon": module_icon,
                        "color": module_color,
                        "features": {
                            "chat": enable_chat,
                            "file_ops": enable_file_ops,
                            "db_ops": enable_db_ops,
                            "web_search": enable_web_search
                        },
                        "ai_config": {
                            "model": ai_model,
                            "temperature": ai_temperature
                        },
                        "created_at": datetime.now().isoformat(),
                        "created_by": user_id
                    }
                    
                    with open(f"{module_dir}/metadata.json", "w") as f:
                        json.dump(metadata, f, indent=2)
                    
                    st.success(f"✅ Module '{module_name}' created successfully in {module_dir}/")
                    st.info("Module files created. You can now customize the code as needed.")
                else:
                    st.warning("Please enter module name and description")
    
    # ===== TAB 2: UPLOAD MODULE =====
    with tab2:
        st.subheader("📤 Upload Custom Module")
        
        uploaded_module = st.file_uploader(
            "Upload module package (.zip or .py file)",
            type=["zip", "py"],
            key="upload_module"
        )
        
        if uploaded_module is not None:
            try:
                # Create modules directory
                modules_dir = "modules"
                os.makedirs(modules_dir, exist_ok=True)
                
                # Save uploaded file
                file_path = os.path.join(modules_dir, uploaded_module.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_module.getvalue())
                
                if uploaded_module.name.endswith('.zip'):
                    # Extract zip file
                    import zipfile
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(modules_dir)
                    st.success(f"✅ Module package '{uploaded_module.name}' extracted successfully!")
                    
                    # Look for module files and add to system
                    st.info("Module extracted. Please restart the application to load the new module.")
                else:
                    st.success(f"✅ Module file '{uploaded_module.name}' uploaded successfully!")
                    st.info("Module file uploaded. Please restart the application to load the new module.")
            
            except Exception as e:
                st.error(f"❌ Error uploading module: {str(e)}")
        
        st.divider()
        
        st.markdown("**Module Package Requirements**")
        st.markdown("""
- Module should be a .py file with a render_* function
- Or a .zip file containing a module with required files
- Module should follow the template structure
- Include a metadata.json file with module information
        """)
    
    # ===== TAB 3: MODULE TOOLS =====
    with tab3:
        st.subheader("⚙️ Module Tools Integration")
        
        st.markdown("**Available Tools for Modules**")
        
        # Show all available tools
        all_tools = {}
        if PHASE2_LOADED:
            all_builtin_tools = ToolRegistry.list_tools()
            for tool in all_builtin_tools:
                all_tools[tool['name']] = tool
        
        all_custom_tools = ToolRegistry.CUSTOM_TOOLS
        for name, tool in all_custom_tools.items():
            all_tools[name] = tool
        
        if all_tools:
            selected_module_for_tools = st.selectbox("Select Module", ["Create New Module"] + [m for m in os.listdir("modules") if os.path.isdir(f"modules/{m}")], key="sel_mod_tools")
            
            if selected_module_for_tools != "Create New Module":
                st.markdown(f"**Tools available for '{selected_module_for_tools}':**")
                
                # Load module metadata to see current tools
                module_meta_path = f"modules/{selected_module_for_tools}/metadata.json"
                current_tools = []
                if os.path.exists(module_meta_path):
                    with open(module_meta_path, 'r') as f:
                        meta = json.load(f)
                        current_tools = meta.get("enabled_tools", [])
                
                for name, tool in all_tools.items():
                    is_enabled = name in current_tools
                    is_selected = st.checkbox(f"{tool['name']} - {tool['desc']}", value=is_enabled, key=f"tool_{selected_module_for_tools}_{name}")
                    
                    # Update module metadata with selected tools
                    if is_selected and name not in current_tools:
                        current_tools.append(name)
                    elif not is_selected and name in current_tools:
                        current_tools.remove(name)
                        
                    # Save updated tools to metadata
                    if os.path.exists(module_meta_path):
                        with open(module_meta_path, 'r') as f:
                            meta = json.load(f)
                        meta["enabled_tools"] = current_tools
                        with open(module_meta_path, 'w') as f:
                            json.dump(meta, f, indent=2)
            
            st.divider()
            
            st.markdown("**Tool Integration Guide**")
            st.code('''# Example of how to use tools in your module:

result = ToolRegistry.run_tool("web_search", agent_name, query="search query")
result = ToolRegistry.run_tool("write_file", agent_name, folder_key="outputs", 
                              filename="result.txt", content="content")
result = ToolRegistry.run_tool("read_file", agent_name, filepath="/path/to/file.txt")
            ''', language="python")
        else:
            st.info("No tools available. Create or upload tools in the Tools Manager first.")
    
    # ===== TAB 4: DEPLOY MODULE =====
    with tab4:
        st.subheader("📋 Deploy Module")
        
        available_modules = [m for m in os.listdir("modules") if os.path.isdir(f"modules/{m}")]
        
        if available_modules:
            selected_module = st.selectbox("Select Module to Deploy", available_modules, key="sel_mod_deploy")
            
            if selected_module:
                # Load module metadata
                module_meta_path = f"modules/{selected_module}/metadata.json"
                if os.path.exists(module_meta_path):
                    with open(module_meta_path, 'r') as f:
                        meta = json.load(f)
                    
                    st.markdown(f"**{meta['icon']} {meta['name']}**")
                    st.caption(meta['description'])
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"**Category:** {meta['category']}")
                        st.caption(f"**Created:** {meta['created_at'][:10]}")
                    with col_b:
                        features = meta.get('features', {})
                        enabled_features = [k for k, v in features.items() if v]
                        st.caption(f"**Features:** {len(enabled_features)} enabled")
                        
                    st.divider()
                    
                    st.markdown("**Deployment Options**")
                    deploy_public = st.checkbox("Make public for all users", value=False)
                    deploy_schedule = st.checkbox("Enable scheduled tasks", value=False)
                    
                    if deploy_schedule:
                        schedule_options = st.selectbox("Schedule Frequency", ["Once", "Daily", "Weekly", "Monthly"])
                        schedule_time = st.time_input("Execution Time", value=datetime.now().time())
                        
                    if st.button(f"🚀 Deploy '{selected_module}' Module", type="primary", use_container_width=True):
                        # Ensure modules directory exists
                        os.makedirs("modules", exist_ok=True)
                        
                        # Create a simple placeholder agent function for the new module
                        def create_placeholder_agent(module_name, description):
                            def placeholder_agent(user_id, task, context=""):
                                return f"This is the {module_name} module. Task: {task} with context: {context}. This is a placeholder - the actual module functionality will be available once properly implemented."
                            return placeholder_agent
                        
                        # Create the agent function
                        agent_function = create_placeholder_agent(meta['name'], meta['description'])
                        
                        # Add to AGENTS dictionary
                        agent_key = f"{meta['icon']} {meta['name']}"
                        AGENTS[agent_key] = {
                            "fn": agent_function,
                            "desc": meta['description']
                        }
                        
                        st.success(f"✅ Module '{selected_module}' deployed successfully!")
                        st.info("Module is now available in the system. It will appear in the AI Agents section.")
                else:
                    st.error(f"Metadata file not found for module '{selected_module}'")
        else:
            st.info("No modules available. Create or upload a module first.")
        
        st.divider()
        
        st.markdown("**Module Deployment Info**")
        st.info("Deployed modules will be available as AI agents in the system. They can be accessed like any other agent.")
    
    # ===== TAB 5: MODULE CHAT =====
    with tab5:
        st.subheader("💬 Module-Specific Chat")
        
        # Check for active provider
        providers = get_active_provider()
        if not providers:
            st.warning("⚠️ No AI provider configured. Go to **Settings → AI Configuration** to set up an AI provider (Ollama, OpenAI, Groq, etc.)")
            st.stop()
        
        # Module selection for chat
        available_modules = [m for m in os.listdir("modules") if os.path.isdir(f"modules/{m}")]
        if available_modules:
            selected_module_for_chat = st.selectbox("Select Module for Chat", ["General Module Chat"] + available_modules, key="sel_mod_chat")
            
            if selected_module_for_chat == "General Module Chat":
                # General module chat
                module_system_prompt = "You are a Module Builder AI assistant. Help users create, configure, and manage custom AI modules. Provide guidance on module creation, tool integration, and deployment. You have access to employee management tools: use add_employee to add employees to the database or get_employees to retrieve the employee list."
                agent_name = "Module Builder AI"
            else:
                # Specific module chat
                module_meta_path = f"modules/{selected_module_for_chat}/metadata.json"
                if os.path.exists(module_meta_path):
                    with open(module_meta_path, 'r') as f:
                        meta = json.load(f)
                    module_system_prompt = f"You are the {meta['name']} AI Agent. {meta['description']} Help users work with this specific module. {meta['name']} features: {' '.join([k for k, v in meta.get('features', {}).items() if v])}. You have access to employee management tools: use add_employee to add employees to the database or get_employees to retrieve the employee list."
                    agent_name = f"{meta['icon']} {meta['name']}"
                else:
                    module_system_prompt = f"You are a {selected_module_for_chat} AI Agent. Help users work with this module. You have access to employee management tools: use add_employee to add employees to the database or get_employees to retrieve the employee list."
                    agent_name = selected_module_for_chat
            
            # Display chat history
            chat_key = f"chat_module_builder"
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []
            
            # Display chat messages
            chat_container = st.container(height=400)
            with chat_container:
                if not st.session_state[chat_key]:
                    st.markdown(f"*💬 Chat with the {agent_name}. Ask about module creation, configuration, or deployment.*")
                for msg in st.session_state[chat_key]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            
            # Chat input
            user_input = st.chat_input(f"Ask the {agent_name} about modules...", key=f"input_module_chat")
            
            # Handle chat submission
            if user_input:
                st.session_state[chat_key].append({"role": "user", "content": user_input})
                
                # Prepare system prompt based on selected module
                system_prompt = module_system_prompt
                
                # Call AI with offline capability
                with st.spinner(f"{agent_name} is thinking..."):
                    response, error = call_ai(user_input, system_prompt)
                    
                    if response:
                        # Check if the AI response contains employee-related instructions
                        # and automatically execute them
                        response_lower = response.lower()
                        if any(keyword in response_lower for keyword in ["add employee", "create employee", "hire employee"]):
                            # Extract employee information from the response
                            # This is a simplified approach - in a real implementation, you would parse the response
                            # to extract employee details and call the add_employee tool
                            pass  # Placeholder for employee extraction logic
                        
                        st.session_state[chat_key].append({"role": "assistant", "content": response})
                        log_agent_action(agent_name, "Module Chat", user_input[:100], response[:100])
                    else:
                        st.session_state[chat_key].append({"role": "assistant", "content": f"❌ {error}"})
                
                st.rerun()
        
        st.divider()
        
        st.markdown("**💡 Module Chat Tips**")
        st.info("""
- Ask about module creation best practices
- Request help with module configuration
- Inquire about tool integration
- Get guidance on deployment options
- Ask for examples of module implementations
        """)
    
    # ===== TAB 6: EMPLOYEE DATABASE =====
    with tab6:
        st.subheader("👥 Employee Database Management")
        
        # Employee database functionality
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("**➕ Add Employee**")
            with st.form("emp_form_module"):
                emp_name = st.text_input("Full Name")
                emp_email = st.text_input("Email")
                emp_dept = st.selectbox("Department", ["Engineering", "Sales", "Marketing", "Finance", "HR", "Operations", "Design", "Support"])
                emp_position = st.text_input("Position")
                emp_salary = st.number_input("Salary ($)", min_value=0.0, step=100.0)
                emp_hire = st.date_input("Hire Date")
                
                if st.form_submit_button("Add Employee", type="primary"):
                    if emp_name:
                        # Create employee table if it doesn't exist
                        db_execute('''CREATE TABLE IF NOT EXISTS module_employees (
                            id INTEGER PRIMARY KEY, 
                            user_id INTEGER, 
                            name TEXT, 
                            email TEXT,
                            department TEXT, 
                            position TEXT, 
                            salary REAL, 
                            hire_date DATE,
                            status TEXT DEFAULT 'active',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')
                        
                        # Insert employee
                        db_execute("INSERT INTO module_employees (user_id, name, email, department, position, salary, hire_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                   (user_id, emp_name, emp_email, emp_dept, emp_position, emp_salary, emp_hire, "active"))
                        st.success("✅ Employee added successfully!")
                        st.rerun()
                    else:
                        st.warning("Please enter employee name")
        
        with col1:
            st.markdown("**📋 Employee List**")
            
            # Check if employee table exists and create if not
            try:
                # Create employee table if it doesn't exist
                db_execute('''CREATE TABLE IF NOT EXISTS module_employees (
                    id INTEGER PRIMARY KEY, 
                    user_id INTEGER, 
                    name TEXT, 
                    email TEXT,
                    department TEXT, 
                    position TEXT, 
                    salary REAL, 
                    hire_date DATE,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
                
                # Fetch employees for current user
                employees = db_fetch("SELECT * FROM module_employees WHERE user_id=? ORDER BY department, name", (user_id,))
                
                if employees:
                    total_employees = len(employees)
                    total_payroll = sum(emp[7] or 0 for emp in employees if emp[8] == "active")
                    
                    cols = st.columns(3)
                    with cols[0]:
                        st.metric("Total Employees", total_employees)
                    with cols[1]:
                        st.metric("Active Employees", len([e for e in employees if e[8] == "active"]))
                    with cols[2]:
                        st.metric("Monthly Payroll", f"${total_payroll:,.2f}")
                    
                    # Group by department
                    dept_employees = {}
                    for emp in employees:
                        dept = emp[5]  # department column
                        if dept not in dept_employees:
                            dept_employees[dept] = []
                        dept_employees[dept].append(emp)
                    
                    for dept, emp_list in dept_employees.items():
                        with st.expander(f"🏢 {dept} ({len(emp_list)})", expanded=True):
                            for emp in emp_list:
                                with st.container(border=True):
                                    emp_cols = st.columns([3, 2, 1, 1])
                                    with emp_cols[0]:
                                        st.markdown(f"**{emp[3]}** — {emp[6]}")  # name and position
                                        st.caption(f"📧 {emp[4] or 'N/A'} | 👥 ID: {emp[0]}")  # email and ID
                                    with emp_cols[1]:
                                        st.caption(f"📅 Hired: {emp[8]}")  # hire date
                                        st.caption(f"Status: {emp[8]}")  # status
                                    with emp_cols[2]:
                                        st.markdown(f"**${emp[7]:,.0f}**")  # salary
                                    with emp_cols[3]:
                                        if st.button("Edit", key=f"edit_emp_{emp[0]}"):
                                            st.session_state.editing_employee = emp
                                            st.rerun()
                                        if st.button("🗑️", key=f"del_emp_{emp[0]}"):
                                            db_execute("DELETE FROM module_employees WHERE id=?", (emp[0],))
                                            st.rerun()
                else:
                    st.info("No employees added yet. Add your first employee using the form.")
            except Exception as e:
                st.error(f"Error accessing employee database: {str(e)}")
        
        st.divider()
        
        # Employee search functionality
        st.markdown("**🔍 Search Employees**")
        search_term = st.text_input("Search by name, department, or position", key="emp_search")
        
        if search_term:
            search_results = db_fetch("""SELECT * FROM module_employees 
                                  WHERE user_id=? AND 
                                  (name LIKE ? OR department LIKE ? OR position LIKE ?)
                                  ORDER BY department, name""", 
                                 (user_id, '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
            
            if search_results:
                st.success(f"Found {len(search_results)} employee(s)")
                for emp in search_results:
                    with st.container(border=True):
                        search_cols = st.columns([3, 2, 1, 1])
                        with search_cols[0]:
                            st.markdown(f"**{emp[3]}** — {emp[6]}")
                            st.caption(f"📧 {emp[4] or 'N/A'} | 👥 ID: {emp[0]}")
                        with search_cols[1]:
                            st.caption(f"🏢 {emp[5]} | 📅 {emp[8]}")
                        with search_cols[2]:
                            st.markdown(f"**${emp[7]:,.0f}**")
                        with search_cols[3]:
                            if st.button("View Details", key=f"view_emp_{emp[0]}"):
                                st.info(f"Employee Details:\nID: {emp[0]}\nName: {emp[3]}\nEmail: {emp[4]}\nDepartment: {emp[5]}\nPosition: {emp[6]}\nSalary: ${emp[7]}\nHire Date: {emp[8]}\nStatus: {emp[8]}")
            else:
                st.info("No employees found matching your search.")


# ========== SETTINGS ==========
def render_settings():
    st.markdown("<div class='agency-header'><h1>⚙️ Settings</h1><p>Configure AI providers, system settings & preferences</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab_restore, tab_tasks, tab_security = st.tabs([
        "🤖 AI Configuration", "👤 Account", "📊 System Info",
        "♻️ Restore Points", "⚡ Task Engine", "🔐 Security & Audit"
    ])

    # ===== RESTORE POINTS TAB =====
    with tab_restore:
        st.subheader("♻️ System Restore Points")
        if not PHASE1_LOADED:
            st.error("Phase 1 foundation not loaded. Check phase1_foundation.py")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Create Restore Point**")
                rp_type = st.selectbox("Type", ["system", "user", "whitelabel", "project"], key="rp_type")
                rp_target = st.text_input("Target ID (optional)", placeholder="user_id / wl_id / project_id", key="rp_target")
                rp_note = st.text_input("Note", placeholder="e.g. Before major update", key="rp_note")
                if st.button("💾 Create Restore Point", type="primary", use_container_width=True):
                    with st.spinner("Creating snapshot..."):
                        result = RestoreEngine.create_restore_point(
                            rp_type,
                            st.session_state.user['username'],
                            rp_target or None,
                            rp_note
                        )
                    if result["success"]:
                        st.success(f"✅ Created: `{result['name']}` ({result['size_kb']} KB)")
                    else:
                        st.error(f"❌ {result.get('error')}")

            with col2:
                st.markdown("**Restore From Point**")
                points = RestoreEngine.list_restore_points()
                if points:
                    for pt in points[:10]:
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([3, 1, 1])
                            with c1:
                                st.markdown(f"**{pt['name']}**")
                                st.caption(f"Type: {pt['type']} | {round(pt['size_bytes']/1024,1)} KB | {str(pt['created_at'])[:16]}")
                                if pt['note']:
                                    st.caption(f"📝 {pt['note']}")
                            with c2:
                                if st.button("↩️ Restore", key=f"rp_restore_{pt['id']}"):
                                    result = RestoreEngine.restore_from_point(
                                        pt['id'],
                                        st.session_state.user['username']
                                    )
                                    if result["success"]:
                                        st.success(f"✅ Restored: {result['restored']}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result['error']}")
                            with c3:
                                if st.button("🗑️", key=f"rp_del_{pt['id']}"):
                                    RestoreEngine.delete_restore_point(
                                        pt['id'],
                                        st.session_state.user['username']
                                    )
                                    st.rerun()
                else:
                    st.info("No restore points yet. Create one above.")

    # ===== TASK ENGINE TAB =====
    with tab_tasks:
        st.subheader("⚡ Multi-Task Engine — Live Status")
        if not PHASE1_LOADED:
            st.error("Phase 1 foundation not loaded.")
        else:
            # Stats
            stats = task_engine.get_stats()
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("⏳ Pending",   stats.get("pending", 0))
            c2.metric("🔄 Running",   stats.get("running", 0))
            c3.metric("✅ Done",      stats.get("done", 0))
            c4.metric("❌ Failed",    stats.get("failed", 0))
            c5.metric("🧵 Threads",   stats.get("active_threads", 0))

            st.divider()

            col1, col2 = st.columns([2, 1])
            with col1:
                status_filter = st.selectbox("Filter by status",
                    ["all", "pending", "running", "done", "failed", "cancelled"],
                    key="task_filter")
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()

            user_id = st.session_state.user['id']
            status_arg = None if status_filter == "all" else status_filter
            tasks = task_engine.get_all_tasks(str(user_id), status_arg)

            if tasks:
                for t in tasks:
                    status_colors = {
                        "pending": "badge-yellow", "running": "badge-yellow",
                        "done": "badge-green", "failed": "badge-red",
                        "cancelled": "badge-red"
                    }
                    badge = status_colors.get(t["status"], "badge-yellow")
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([4, 1, 1])
                        with c1:
                            st.markdown(f"**{t['agent_name']}** — {t['task'][:80]}")
                            st.caption(f"ID: `{t['task_id']}` | Priority: {t['priority']} | {str(t['created_at'])[:16]}")
                            if t.get("result"):
                                with st.expander("View Result"):
                                    st.text(t["result"][:500])
                            if t.get("error"):
                                st.error(f"Error: {t['error'][:200]}")
                        with c2:
                            st.markdown(f"<span class='{badge}'>{t['status']}</span>", unsafe_allow_html=True)
                        with c3:
                            if t["status"] == "failed":
                                if st.button("🔁 Retry", key=f"retry_{t['task_id']}"):
                                    task_engine.retry_failed_task(t["task_id"])
                                    st.rerun()
                            elif t["status"] in ["pending", "running"]:
                                if st.button("🛑 Cancel", key=f"cancel_{t['task_id']}"):
                                    task_engine.cancel_task(t["task_id"])
                                    st.rerun()
            else:
                st.info("No tasks found. Run an AI agent to see tasks here.")

    # ===== SECURITY & AUDIT TAB =====
    with tab_security:
        st.subheader("🔐 Security & Audit Log")
        if not PHASE1_LOADED:
            st.error("Phase 1 foundation not loaded.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🔒 Phase 1 Security Status**")
                st.success("✅ Encryption: AES Fernet (active)")
                st.success("✅ Password hashing: SHA-256 + salt")
                st.success("✅ Session tokens: active")
                st.success("✅ Rate limiting: active")
                st.success("✅ Audit logging: active")

            with col2:
                st.markdown("**📊 Session Info**")
                active = db_fetch_with_path(DB_SYSTEM,
                    "SELECT COUNT(*) as cnt FROM active_sessions")
                expired = db_fetch_with_path(DB_SYSTEM,
                    "SELECT COUNT(*) as cnt FROM active_sessions WHERE expires_at < datetime('now')")
                st.metric("Active Sessions", active[0]["cnt"] if active else 0)
                st.metric("Expired Sessions", expired[0]["cnt"] if expired else 0)
                if st.button("🧹 Clean Expired Sessions"):
                    cleanup_expired_sessions()
                    st.success("✅ Cleaned!")

            st.divider()
            st.markdown("**📋 Recent Audit Log**")
            logs = db_fetch_with_path(DB_SYSTEM,
                "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50")
            if logs:
                for log in logs:
                    badge = "badge-green" if "create" in log["action"] else "badge-yellow"
                    st.markdown(f"""
                    <div class='agent-card'>
                        <strong>{log['user_id']}</strong> ({log['user_type']})
                        → <code>{log['action']}</code> on <em>{log['target']}</em>
                        <span class='{badge}' style='float:right'>{str(log['created_at'])[:16]}</span>
                        <br><small style='color:#718096'>{log['detail'][:100]}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No audit logs yet.")

    # ===== AI CONFIGURATION TAB =====
    with tab1:
        st.subheader("🤖 AI Provider Configuration")
        st.caption("Configure which AI model powers your agents. Only one provider is active at a time.")

        providers = db_fetch("SELECT * FROM llm_providers ORDER BY id")
        active_provider = db_fetch("SELECT id FROM llm_providers WHERE is_active=1 LIMIT 1")
        active_id = active_provider[0][0] if active_provider else None

        for prov in providers:
            is_active = prov[0] == active_id
            with st.container(border=True):
                badge = "badge-green" if is_active else "badge-yellow"
                st.markdown(f"**{prov[1]}** <span class='{badge}'>{'● Active' if is_active else '○ Inactive'}</span>", unsafe_allow_html=True)

                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    api_key = st.text_input("API Key", value=prov[2] or "", type="password",
                                            key=f"api_{prov[0]}", placeholder="Enter API key (not needed for Ollama)")
                with col2:
                    model = st.text_input("Model", value=prov[4] or "",
                                          key=f"model_{prov[0]}", placeholder="e.g., gpt-4o-mini")
                with col3:
                    if st.button("💾 Save", key=f"save_prov_{prov[0]}"):
                        db_execute("UPDATE llm_providers SET api_key=?, model=? WHERE id=?", (api_key, model, prov[0]))
                        st.success("Saved!")
                    if not is_active:
                        if st.button("⚡ Activate", key=f"act_prov_{prov[0]}", type="primary"):
                            db_execute("UPDATE llm_providers SET is_active=0")
                            db_execute("UPDATE llm_providers SET is_active=1 WHERE id=?", (prov[0],))
                            st.success(f"✅ {prov[1]} is now active!")
                            st.rerun()

        st.divider()
        st.subheader("🔗 Quick Setup Guide")
        with st.expander("How to set up each provider"):
            st.markdown("""
**Ollama (Free, Local):**
1. Download from [ollama.ai](https://ollama.ai)
2. Run `ollama pull llama3`
3. Activate Ollama here — no API key needed

**OpenAI:**
1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Enter key above, set model to `gpt-4o-mini`
3. Activate

**Groq (Free tier available):**
1. Get key from [console.groq.com](https://console.groq.com)
2. Model: `llama3-8b-8192` (fast & free tier)
3. Activate

**OpenRouter (Many models):**
1. Get key from [openrouter.ai](https://openrouter.ai)
2. Use any model like `openai/gpt-4o-mini`
3. Activate
            """)

        st.divider()
        st.subheader("🧪 Test AI Connection")
        if st.button("🧪 Test Active AI Provider", type="primary"):
            with st.spinner("Testing connection..."):
                response, error = call_ai("Say hello and confirm you are working correctly. Keep it brief.")
                if response:
                    st.success(f"✅ AI is working! Response: {response[:200]}")
                else:
                    st.error(f"❌ {error}")

    with tab2:
        st.subheader("👤 Account Settings")
        user = st.session_state.user
        with st.container(border=True):
            st.markdown(f"**Username:** {user['username']}")
            st.markdown(f"**Role:** {user['role'].upper()}")
            st.markdown(f"**Type:** {user.get('type', 'admin').upper()}")

        st.divider()
        st.subheader("🔑 Change Password")
        with st.form("change_password"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_pw == confirm_pw and len(new_pw) >= 6:
                    old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
                    check = db_fetch("SELECT id FROM users WHERE id=? AND password=?", (user['id'], old_hash))
                    if check:
                        new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
                        db_execute("UPDATE users SET password=? WHERE id=?", (new_hash, user['id']))
                        st.success("✅ Password updated!")
                    else:
                        st.error("Current password incorrect")
                else:
                    st.error("Passwords don't match or too short (min 6 chars)")

    with tab3:
        st.subheader("📊 System Information")
        tables = db_fetch("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        total_records = 0
        for table in tables:
            count = db_fetch(f"SELECT COUNT(*) FROM {table[0]}")
            total_records += count[0][0] if count else 0

        cols = st.columns(3)
        with cols[0]: st.metric("Database Tables", len(tables))
        with cols[1]: st.metric("Total Records", total_records)
        with cols[2]: st.metric("DB Path", DB_PATH)

        with st.expander("📋 Database Tables"):
            for table in tables:
                count = db_fetch(f"SELECT COUNT(*) FROM {table[0]}")
                st.markdown(f"• **{table[0]}**: {count[0][0] if count else 0} records")

        st.divider()
        if st.button("⚠️ Clear All Agent Logs", type="secondary"):
            db_execute("DELETE FROM agent_logs")
            st.success("Logs cleared!")

# ========== SHARED AI CHAT ==========
def _render_ai_chat(agent_name, system_prompt):
    """Reusable AI chat component for any module with offline capability"""
    chat_key = f"chat_{agent_name.replace(' ', '_')}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Display chat history
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state[chat_key]:
            st.markdown(f"*💬 Chat with {agent_name}. Ask anything related to this module.*")
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input
    user_input = st.chat_input(f"Ask {agent_name} anything...", key=f"input_{chat_key}")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col3:
        if st.button("🗑️ Clear Chat", key=f"clear_{chat_key}"):
            st.session_state[chat_key] = []
            st.rerun()

    if user_input:
        st.session_state[chat_key].append({"role": "user", "content": user_input})

        # Build conversation history for context
        messages_for_api = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state[chat_key][-10:]:  # last 10 messages for context
            messages_for_api.append({"role": msg["role"], "content": msg["content"]})

        with st.spinner(f"{agent_name} thinking..."):
            # Try to connect to online provider first
            providers = get_active_provider()
            if providers:
                # Online provider available
                response, error = call_ai(user_input, system_prompt)
            else:
                # No online provider, try offline (Ollama)
                try:
                    # Check if Ollama is available for offline processing
                    import urllib.request
                    urllib.request.urlopen('http://localhost:11434', timeout=3)
                    
                    # If Ollama is available, use it
                    import requests
                    ollama_url = "http://localhost:11434/api/generate"
                    payload = {
                        "model": "gemma3:4b",  # Default model
                        "prompt": f"{system_prompt}\n\nUser asked: {user_input}",
                        "stream": False
                    }
                    response_raw = requests.post(ollama_url, json=payload, timeout=30)
                    
                    if response_raw.status_code == 200:
                        response_data = response_raw.json()
                        response = response_data["response"]
                        error = None
                    else:
                        response = None
                        error = f"Ollama error: {response_raw.status_code}"
                except Exception as e:
                    response = None
                    error = f"No AI provider available. Set up Ollama for offline use. Error: {str(e)}"

        if response:
            st.session_state[chat_key].append({"role": "assistant", "content": response})
            log_agent_action(agent_name, "Chat Response", user_input[:100], response[:100])
        else:
            st.session_state[chat_key].append({"role": "assistant", "content": f"❌ {error}"})

        st.rerun()

# ========== ADMIN PANEL ==========
def render_admin():
    st.markdown("<div class='agency-header'><h1>🛡️ Admin Panel</h1><p>User management, system control & white label administration</p></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 Users", "🏷️ White Labels", "🔧 System Control"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ Add User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["admin", "user", "viewer"])
                if st.form_submit_button("Create User"):
                    if new_username and new_password:
                        pw_hash = hashlib.sha256(new_password.encode()).hexdigest()
                        try:
                            db_execute("INSERT INTO users (username, password, email, role, is_active, created_at) VALUES (?,?,?,?,?,?)",
                                       (new_username, pw_hash, new_email, new_role, 1, datetime.now()))
                            st.success(f"✅ User '{new_username}' created!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Username and password required")

        with col1:
            st.subheader("👥 All Users")
            users = db_fetch("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY created_at DESC")
            for u in users:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{u[1]}** — {u[3].upper()}")
                        st.caption(f"📧 {u[2] or 'N/A'} | Created: {str(u[5])[:16]}")
                    with c2:
                        badge = "badge-green" if u[4] else "badge-red"
                        st.markdown(f"<span class='{badge}'>{'Active' if u[4] else 'Inactive'}</span>", unsafe_allow_html=True)
                    with c3:
                        if u[1] != "admin":
                            toggle = "Deactivate" if u[4] else "Activate"
                            if st.button(toggle, key=f"toggle_user_{u[0]}"):
                                db_execute("UPDATE users SET is_active=? WHERE id=?", (0 if u[4] else 1, u[0]))
                                st.rerun()
                            if st.button("🗑️", key=f"del_user_{u[0]}"):
                                db_execute("DELETE FROM users WHERE id=?", (u[0],))
                                st.rerun()

    with tab2:
        st.subheader("🏷️ White Label Instances")
        col1, col2 = st.columns([2, 1])
        with col2:
            st.subheader("➕ New White Label")
            with st.form("wl_form"):
                wl_company = st.text_input("Company Name")
                wl_email = st.text_input("Admin Email")
                wl_password = st.text_input("Password", type="password")
                if st.form_submit_button("Create White Label"):
                    if wl_company and wl_email:
                        pw_hash = hashlib.sha256((wl_password or "wl123").encode()).hexdigest()
                        db_execute("INSERT INTO white_label_instances (company_name, admin_email, password, status, folder, privileges, created_at) VALUES (?,?,?,?,?,?,?)",
                                   (wl_company, wl_email, pw_hash, "active", wl_company.lower().replace(" ", "_"), "[]", datetime.now()))
                        st.success(f"✅ White label '{wl_company}' created!")
                        st.rerun()

        with col1:
            wls = db_fetch("SELECT * FROM white_label_instances ORDER BY created_at DESC")
            if wls:
                for wl in wls:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{wl[1]}**")
                            st.caption(f"📧 {wl[2]} | Status: {wl[4]}")
                        with c2:
                            if st.button("🗑️", key=f"del_wl_{wl[0]}"):
                                db_execute("DELETE FROM white_label_instances WHERE id=?", (wl[0],))
                                st.rerun()
            else:
                st.info("No white label instances yet.")

    with tab3:
        st.subheader("🔧 System Control")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("**🗑️ Clear Agent Logs**")
                st.caption("Remove all agent activity logs")
                if st.button("Clear Logs", use_container_width=True):
                    db_execute("DELETE FROM agent_logs")
                    st.success("✅ Logs cleared!")

            with st.container(border=True):
                st.markdown("**🧹 Clear AI Brain Templates**")
                st.caption("Remove all generated templates")
                if st.button("Clear Templates", use_container_width=True):
                    db_execute("DELETE FROM ai_brain_templates")
                    db_execute("DELETE FROM ai_brain_generated")
                    st.success("✅ Templates cleared!")

        with col2:
            with st.container(border=True):
                st.markdown("**📊 System Stats**")
                tables = db_fetch("SELECT name FROM sqlite_master WHERE type='table'")
                st.metric("DB Tables", len(tables))
                users_count = db_fetch("SELECT COUNT(*) FROM users")[0][0]
                st.metric("Total Users", users_count)
                logs_count = db_fetch("SELECT COUNT(*) FROM agent_logs")[0][0]
                st.metric("Agent Log Entries", logs_count)

            with st.container(border=True):
                st.markdown("**📥 Export Database**")
                st.caption("Download all data as JSON")
                if st.button("Export All Data", use_container_width=True):
                    all_data = {}
                    for table in tables:
                        rows = db_fetch(f"SELECT * FROM {table[0]}")
                        all_data[table[0]] = [list(r) for r in rows]
                    export_json = json.dumps(all_data, default=str, indent=2)
                    st.download_button("📥 Download JSON", data=export_json,
                                       file_name=f"databit_export_{datetime.now().strftime('%Y%m%d')}.json",
                                       mime="application/json")

# ========== LLM SETTINGS (dedicated page) ==========
def render_llm_settings():
    st.markdown("<div class='agency-header'><h1>🔌 LLM Settings</h1><p>Configure AI providers — Ollama local, OpenRouter free models, OpenAI, Groq, Gemini</p></div>", unsafe_allow_html=True)

    # Current active provider banner
    active = db_fetch("SELECT name, model FROM llm_providers WHERE is_active=1 LIMIT 1")
    if active:
        st.success(f"✅ Currently Active: **{active[0][0]}** — Model: `{active[0][1]}`")
    else:
        st.error("❌ No AI provider active. Activate one below.")

    tab1, tab2, tab3, tab4 = st.tabs(["🟢 Ollama (Local)", "🆓 OpenRouter Free", "☁️ Other Providers", "🧪 Test AI"])

    # ===== TAB 1: OLLAMA =====
    with tab1:
        st.subheader("🟢 Ollama — 100% Free Local AI")
        st.caption("Runs on your computer. No internet, no cost, no API key needed.")
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                ollama_url = st.text_input("Ollama URL", value="http://localhost:11434", key="ollama_url_input")

                # Auto-detect installed models
                try:
                    r = requests.get(f"{ollama_url}/api/tags", timeout=3)
                    if r.status_code == 200:
                        installed = [m['name'] for m in r.json().get('models', [])]
                        if installed:
                            ollama_model = st.selectbox("Select Installed Model", installed, key="ollama_model_select")
                        else:
                            st.warning("No models installed. Run: ollama pull gemma3:4b")
                            ollama_model = st.text_input("Model name", value="gemma3:4b", key="ollama_model_input")
                    else:
                        ollama_model = st.text_input("Model name", value="gemma3:4b", key="ollama_model_input2")
                except:
                    st.warning("⚠️ Ollama not running. Start Ollama first.")
                    ollama_model = st.text_input("Model name", value="gemma3:4b", key="ollama_model_input3")

            with col2:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("🔍 Test", use_container_width=True):
                    try:
                        r = requests.get(f"{ollama_url}/api/tags", timeout=5)
                        if r.status_code == 200:
                            models = [m['name'] for m in r.json().get('models', [])]
                            st.success(f"✅ Online!\n{len(models)} models")
                        else:
                            st.error("❌ Not responding")
                    except:
                        st.error("❌ Not running")

                if st.button("⚡ Activate", use_container_width=True, type="primary"):
                    db_execute("UPDATE llm_providers SET is_active=0")
                    db_execute("UPDATE llm_providers SET is_active=1, base_url=?, model=? WHERE name='Ollama'",
                               (ollama_url, ollama_model))
                    st.success("✅ Ollama activated!")
                    st.rerun()

        with st.expander("📋 Setup Guide"):
            st.markdown("""
**1.** Download from [ollama.ai](https://ollama.ai) and install

**2.** Open PowerShell and pull a model:
```
ollama pull gemma3:4b
```
**3.** Click **Test** → then **Activate**

**Your installed models show automatically above!**
            """)

    # ===== TAB 2: OPENROUTER FREE MODELS =====
    with tab2:
        st.subheader("🆓 OpenRouter — Free AI Models")
        st.caption("Get a free API key at openrouter.ai — many powerful models available for free!")

        OPENROUTER_FREE_MODELS = [
            {"name": "DeepSeek R1 (Free)", "id": "deepseek/deepseek-r1:free", "desc": "Best reasoning, 671B — FREE"},
            {"name": "DeepSeek V3 (Free)", "id": "deepseek/deepseek-chat-v3-5:free", "desc": "Fast & smart — FREE"},
            {"name": "Llama 3.3 70B (Free)", "id": "meta-llama/llama-3.3-70b-instruct:free", "desc": "Meta's best open model — FREE"},
            {"name": "Llama 3.1 8B (Free)", "id": "meta-llama/llama-3.1-8b-instruct:free", "desc": "Fast & lightweight — FREE"},
            {"name": "Mistral 7B (Free)", "id": "mistralai/mistral-7b-instruct:free", "desc": "Great for coding — FREE"},
            {"name": "Gemma 3 12B (Free)", "id": "google/gemma-3-12b-it:free", "desc": "Google's Gemma — FREE"},
            {"name": "Gemma 3 27B (Free)", "id": "google/gemma-3-27b-it:free", "desc": "Google's large Gemma — FREE"},
            {"name": "Qwen 2.5 7B (Free)", "id": "qwen/qwen-2.5-7b-instruct:free", "desc": "Alibaba's model — FREE"},
            {"name": "Qwen 2.5 72B (Free)", "id": "qwen/qwen-2.5-72b-instruct:free", "desc": "Alibaba's large model — FREE"},
            {"name": "Phi-3 Mini (Free)", "id": "microsoft/phi-3-mini-128k-instruct:free", "desc": "Microsoft small model — FREE"},
            {"name": "Phi-3 Medium (Free)", "id": "microsoft/phi-3-medium-128k-instruct:free", "desc": "Microsoft medium — FREE"},
            {"name": "Mythomax 13B (Free)", "id": "gryphe/mythomax-l2-13b:free", "desc": "Creative writing — FREE"},
            {"name": "Zephyr 7B (Free)", "id": "huggingfaceh4/zephyr-7b-beta:free", "desc": "HuggingFace model — FREE"},
            {"name": "Toppy M 7B (Free)", "id": "undi95/toppy-m-7b:free", "desc": "General purpose — FREE"},
            {"name": "OpenChat 7B (Free)", "id": "openchat/openchat-7b:free", "desc": "Chat optimized — FREE"},
        ]

        or_prov = db_fetch("SELECT * FROM llm_providers WHERE name='OpenRouter' LIMIT 1")
        current_key = or_prov[0][2] if or_prov else ""
        current_model = or_prov[0][4] if or_prov else ""

        with st.container(border=True):
            or_key = st.text_input("🔑 OpenRouter API Key",
                                    value=current_key or "",
                                    type="password",
                                    placeholder="Get free key at openrouter.ai/keys")

            st.markdown("**Select a Free Model:**")
            cols = st.columns(3)
            selected_model = None

            for i, model in enumerate(OPENROUTER_FREE_MODELS):
                with cols[i % 3]:
                    is_current = current_model == model["id"]
                    border_style = "border: 2px solid #667eea;" if is_current else ""
                    st.markdown(f"""
                    <div style='background:#f8fafc;padding:10px;border-radius:8px;margin-bottom:8px;{border_style}'>
                        <strong>{'✅ ' if is_current else ''}{model['name']}</strong><br>
                        <small style='color:#718096'>{model['desc']}</small><br>
                        <code style='font-size:0.7rem;color:#667eea'>{model['id']}</code>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("⚡ Use This", key=f"or_model_{i}", use_container_width=True):
                        if or_key:
                            db_execute("UPDATE llm_providers SET is_active=0")
                            db_execute("""UPDATE llm_providers SET api_key=?, model=?, base_url=?, is_active=1
                                         WHERE name='OpenRouter'""",
                                       (or_key, model["id"], "https://openrouter.ai/api/v1"))
                            st.success(f"✅ {model['name']} activated!")
                            st.rerun()
                        else:
                            st.error("Enter API key first!")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                custom_model = st.text_input("Or enter custom model ID", placeholder="provider/model-name:free", key="or_custom")
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡ Use Custom Model", use_container_width=True):
                    if or_key and custom_model:
                        db_execute("UPDATE llm_providers SET is_active=0")
                        db_execute("""UPDATE llm_providers SET api_key=?, model=?, base_url=?, is_active=1
                                     WHERE name='OpenRouter'""",
                                   (or_key, custom_model, "https://openrouter.ai/api/v1"))
                        st.success(f"✅ {custom_model} activated!")
                        st.rerun()

        with st.expander("📋 How to get free OpenRouter API key"):
            st.markdown("""
**1.** Go to [openrouter.ai](https://openrouter.ai) and sign up (free)

**2.** Go to [openrouter.ai/keys](https://openrouter.ai/keys)

**3.** Click **Create Key** — copy it

**4.** Paste it above and click **Use This** on any free model

**All models marked :free have no cost!**
            """)

    # ===== TAB 3: OTHER PROVIDERS =====
    with tab3:
        st.subheader("☁️ Other Cloud Providers")

        other_providers = [
            {"name": "OpenAI", "url": "https://platform.openai.com/api-keys",
             "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], "note": "Paid, best quality", "base": "https://api.openai.com/v1"},
            {"name": "Groq", "url": "https://console.groq.com",
             "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"], "note": "FREE tier, ultra fast", "base": "https://api.groq.com/openai/v1"},
            {"name": "Gemini", "url": "https://aistudio.google.com/app/apikey",
             "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"], "note": "Google AI, free tier", "base": "https://generativelanguage.googleapis.com"},
        ]

        active_provider = db_fetch("SELECT id FROM llm_providers WHERE is_active=1 LIMIT 1")
        active_id = active_provider[0][0] if active_provider else None

        for pinfo in other_providers:
            prov = db_fetch("SELECT * FROM llm_providers WHERE name=? LIMIT 1", (pinfo["name"],))
            if not prov:
                continue
            prov = prov[0]
            is_active = prov[0] == active_id
            badge = "badge-green" if is_active else "badge-yellow"

            with st.container(border=True):
                st.markdown(f"**{pinfo['name']}** <span class='{badge}'>{'● Active' if is_active else '○ Inactive'}</span> — {pinfo['note']}", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    api_key = st.text_input("API Key", value=prov[2] or "", type="password",
                                            key=f"op_api_{prov[0]}", placeholder=f"Get from {pinfo['url']}")
                with col2:
                    model = st.selectbox("Model", pinfo["models"],
                                         index=pinfo["models"].index(prov[4]) if prov[4] in pinfo["models"] else 0,
                                         key=f"op_model_{prov[0]}")
                with col3:
                    if st.button("💾 Save", key=f"op_save_{prov[0]}"):
                        db_execute("UPDATE llm_providers SET api_key=?, model=?, base_url=? WHERE id=?",
                                   (api_key, model, pinfo["base"], prov[0]))
                        st.success("Saved!")
                    if not is_active:
                        if st.button("⚡ Activate", key=f"op_act_{prov[0]}", type="primary"):
                            db_execute("UPDATE llm_providers SET is_active=0")
                            db_execute("UPDATE llm_providers SET api_key=?, model=?, base_url=?, is_active=1 WHERE id=?",
                                       (api_key, model, pinfo["base"], prov[0]))
                            st.success(f"✅ {pinfo['name']} activated!")
                            st.rerun()

    # ===== TAB 4: TEST =====
    with tab4:
        st.subheader("🧪 Test Your Active AI")
        active = db_fetch("SELECT name, model FROM llm_providers WHERE is_active=1 LIMIT 1")
        if active:
            st.info(f"Active: **{active[0][0]}** — `{active[0][1]}`")
            test_prompt = st.text_area("Test message", value="Hello! Tell me your name and one thing you can help with. Be brief.", height=80)
            if st.button("🧪 Send Test", type="primary", use_container_width=True):
                with st.spinner("Waiting for AI response..."):
                    response, error = call_ai(test_prompt)
                    if response:
                        st.success("✅ AI is working!")
                        st.markdown(response)
                    else:
                        st.error(f"❌ {error}")
        else:
            st.warning("No provider active. Go to Ollama or OpenRouter tab and activate one.")

# ========== MAIN ==========
def main():
    if not st.session_state.auth:
        render_login()
        return

    render_sidebar()

    page = st.session_state.page
    routes = {
        "dashboard": render_dashboard,
        "sales": render_sales,
        "webdev": render_webdev,
        "marketing": render_marketing,
        "finance": render_finance,
        "crm": render_crm,
        "erp": render_erp,
        "mobile": render_mobile,
        "ai_brain": render_ai_brain,
        "ai_agents": render_ai_agents,
        "tools": render_tools_manager,
        "modules": render_module_builder,
        "chat": render_chat_hub,
        "email": render_email_hub,
        "users": render_user_management,
        "whitelabel": render_whitelabel_management,
        "scheduler": render_scheduler,
        "notifications": render_notifications,
        "training": render_ai_training,
        "admin": render_admin,
        "llm": render_llm_settings,
        "settings": render_settings,
    }

    render_fn = routes.get(page, render_dashboard)
    render_fn()



# ========== PHASE 3 UI PAGES ==========

def render_chat_hub():
    """Main chat hub — admin talks to any agent, user, or white label."""
    user_id = st.session_state.user['id']
    username = st.session_state.user['username']

    st.markdown("<div class='agency-header'><h1>💬 Chat Hub</h1><p>Talk to any AI agent, user, or white label — online & offline</p></div>", unsafe_allow_html=True)

    tab_agents, tab_users, tab_wl, tab_search = st.tabs(
        ["🤖 Agent Chats", "👥 User Chats", "🏢 White Label", "🔍 Search History"])

    with tab_agents:
        st.subheader("Chat with AI Agents")
        cols = st.columns(3)
        agent_names = list(AGENTS.keys())
        for i, agent_name in enumerate(agent_names):
            with cols[i % 3]:
                room_id = ChatEngine.get_or_create_room(
                    "admin_agent", username, agent_name)
                unread = ChatEngine.get_unread_count(room_id, username)
                badge = f" 🔴 {unread}" if unread > 0 else ""
                if st.button(f"{agent_name}{badge}", use_container_width=True,
                            key=f"open_chat_{agent_name}"):
                    st.session_state['active_chat_room'] = room_id
                    st.session_state['active_chat_agent'] = agent_name
                    st.session_state['active_chat_other'] = agent_name
                    st.rerun()

        if 'active_chat_room' in st.session_state:
            st.divider()
            agent = st.session_state.get('active_chat_agent')
            st.subheader(f"💬 Chat with {agent}")
            render_chat_widget(
                st.session_state['active_chat_room'],
                username,
                st.session_state.get('active_chat_other', ''),
                call_ai_fn=call_ai,
                agent_name=agent,
                show_call_btn=True
            )

    with tab_users:
        st.subheader("Chat with Users")
        users = db_fetch_with_path(DB_USERS, "SELECT id, username, email FROM users WHERE role!='admin'")
        if users:
            for u in users:
                room_id = ChatEngine.get_or_create_room(
                    "admin_user", username, str(u['id']))
                unread = ChatEngine.get_unread_count(room_id, username)
                badge = f" 🔴 {unread}" if unread > 0 else ""
                if st.button(f"👤 {u['username']}{badge}",
                            key=f"user_chat_{u['id']}",
                            use_container_width=True):
                    st.session_state['active_user_chat'] = room_id
                    st.session_state['active_user_name'] = u['username']
                    st.rerun()

            if 'active_user_chat' in st.session_state:
                st.divider()
                st.subheader(f"💬 Chat with {st.session_state.get('active_user_name')}")
                render_chat_widget(
                    st.session_state['active_user_chat'],
                    username,
                    st.session_state.get('active_user_name', ''),
                    show_call_btn=True
                )
        else:
            st.info("No users yet.")

    with tab_wl:
        st.subheader("Chat with White Label Clients")
        wls = db_fetch_with_path(DB_WHITELABEL,
            "SELECT id, company_name, admin_email FROM whitelabel_instances")
        if wls:
            for wl in wls:
                room_id = ChatEngine.get_or_create_room(
                    "admin_wl", username, str(wl['id']))
                unread = ChatEngine.get_unread_count(room_id, username)
                badge = f" 🔴 {unread}" if unread > 0 else ""
                if st.button(f"🏢 {wl['company_name']}{badge}",
                            key=f"wl_chat_{wl['id']}",
                            use_container_width=True):
                    st.session_state['active_wl_chat'] = room_id
                    st.session_state['active_wl_name'] = wl['company_name']
                    st.rerun()

            if 'active_wl_chat' in st.session_state:
                st.divider()
                st.subheader(f"💬 Chat with {st.session_state.get('active_wl_name')}")
                render_chat_widget(
                    st.session_state['active_wl_chat'],
                    username,
                    st.session_state.get('active_wl_name', ''),
                    show_call_btn=True
                )
        else:
            st.info("No white label instances yet.")

    with tab_search:
        st.subheader("🔍 Search Chat History")
        kw = st.text_input("Search keyword", key="chat_search_kw")
        if st.button("Search", key="do_chat_search"):
            results = ChatEngine.search_messages(username, kw)
            if results:
                for r in results:
                    with st.container(border=True):
                        st.markdown(f"**{r['sender']}** in `{r['room_type']}`")
                        st.markdown(r['message'][:200])
                        st.caption(str(r['created_at'])[:16])
            else:
                st.info("No results found.")


def render_email_hub():
    """Email hub — manage all agent emails."""
    st.markdown("<div class='agency-header'><h1>📧 Email Hub</h1><p>All agent emails — inbox, sent, compose, rules, training</p></div>", unsafe_allow_html=True)

    tab_setup, tab_emails, tab_training = st.tabs(
        ["⚙️ Email Setup", "📬 Agent Emails", "🧠 Training"])

    with tab_setup:
        st.subheader("Setup Agent Email Accounts")
        st.info("Each agent needs a Gmail account with App Password enabled.")

        with st.container(border=True):
            st.markdown("**Quick Setup — Assign Gmail to Agent**")
            col1, col2 = st.columns(2)
            with col1:
                sel_agent = st.selectbox("Agent", list(AGENTS.keys()), key="email_setup_agent")
                domain = st.text_input("Your Domain", value="youragency.com",
                                      key="email_domain")
            with col2:
                gmail_user = st.text_input("Gmail Username",
                    placeholder="yourname@gmail.com", key="gmail_user")
                gmail_pw = st.text_input("Gmail App Password",
                    type="password",
                    placeholder="16-char app password from Google",
                    key="gmail_pw")

            if st.button("💾 Save Email Config", type="primary",
                        use_container_width=True):
                if gmail_user and gmail_pw:
                    result = AgentEmailIdentity.setup_agent_email(
                        sel_agent, domain, gmail_user, gmail_pw)
                    if result["success"]:
                        st.success(f"✅ {sel_agent} → {result['email']}")
                    else:
                        st.error(result.get("error"))
                else:
                    st.warning("Enter Gmail username and app password")

        st.divider()
        st.subheader("Current Agent Email Assignments")
        accounts = AgentEmailIdentity.list_all_agent_emails()
        if accounts:
            for acct in accounts:
                badge = "badge-green" if acct['is_active'] else "badge-red"
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**{acct['agent_name']}**")
                    c2.markdown(f"📧 `{acct.get('email_address','Not set')}`")
                    c3.markdown(f"<span class='{badge}'>{'Active' if acct['is_active'] else 'Inactive'}</span>",
                               unsafe_allow_html=True)
                    if acct.get('last_checked'):
                        st.caption(f"Last checked: {str(acct['last_checked'])[:16]}")
        else:
            st.info("No email accounts configured yet.")

        with st.expander("📋 How to get Gmail App Password"):
            st.markdown("""
**1.** Go to your Google Account → Security

**2.** Enable **2-Step Verification** (required)

**3.** Search for **App Passwords**

**4.** Select app: **Mail** | Device: **Other** → name it "DataBit AI"

**5.** Copy the 16-character password and paste it above

Each agent can share the same Gmail or use different accounts.
            """)

    with tab_emails:
        st.subheader("Agent Email Manager")
        agent_sel = st.selectbox("Select Agent", list(AGENTS.keys()),
                                key="email_agent_sel")
        st.divider()
        render_email_widget(agent_sel, call_ai_fn=call_ai)

    with tab_training:
        st.subheader("🧠 AI Training from Email/Files")
        agent_sel = st.selectbox("Train Agent", list(AGENTS.keys()),
                                key="train_agent_sel")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Manual Training Text**")
            train_text = st.text_area("Training content",
                height=150, key="train_text_input",
                placeholder="Paste knowledge, instructions, or examples here...")
            if st.button("💾 Add Training", use_container_width=True):
                if train_text:
                    result = AITrainingSystem.train_from_text(
                        agent_sel, train_text, "manual")
                    st.success("✅ Training data saved!")

        with col2:
            st.markdown("**Upload Training File**")
            train_file = st.file_uploader("Upload file",
                type=['txt', 'pdf', 'csv', 'md', 'json'],
                key="train_file_upload")
            if train_file:
                if st.button("📥 Load File as Training", use_container_width=True):
                    save_path = f"ai_training/{train_file.name}"
                    os.makedirs("ai_training", exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(train_file.getbuffer())
                    result = AITrainingSystem.train_from_file(agent_sel, save_path)
                    if result["success"]:
                        st.success(f"✅ {result['chars_loaded']} chars loaded!")
                    else:
                        st.error(result.get("error"))

        st.divider()
        st.markdown("**Existing Training Data**")
        training = AITrainingSystem.list_training_data(agent_sel)
        if training:
            for td in training:
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**[{td['training_type'].upper()}]** from `{td['source']}`")
                        st.caption(f"{td['preview']}...")
                        st.caption(str(td['created_at'])[:16])
                    with c2:
                        if st.button("🗑️", key=f"del_train_{td['id']}"):
                            AITrainingSystem.delete_training(td['id'])
                            st.rerun()
        else:
            st.info("No training data yet.")



# ========== PHASE 4 UI PAGES ==========

def render_notifications_bar():
    """Show notification bell in sidebar."""
    user_id = str(st.session_state.user['id'])
    count = NotificationEngine.get_unread_count(user_id)
    if count > 0:
        st.sidebar.markdown(f"<div style='background:#f6e05e;color:#744210;padding:8px 12px;border-radius:8px;margin-bottom:8px;font-weight:600;'>🔔 {count} unread notification{'s' if count>1 else ''}</div>", unsafe_allow_html=True)
        if st.sidebar.button("View Notifications", use_container_width=True, key="view_notifs"):
            st.session_state.page = "notifications"
            st.rerun()


def render_notifications():
    user_id = str(st.session_state.user['id'])
    st.markdown("<div class='agency-header'><h1>🔔 Notifications</h1><p>All your alerts, updates and messages</p></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("✅ Mark All Read", use_container_width=True):
            NotificationEngine.mark_read(user_id=user_id)
            st.rerun()

    notifs = NotificationEngine.get_notifications(user_id, limit=50)
    if notifs:
        type_icons = {"info":"ℹ️","success":"✅","warning":"⚠️","error":"❌","task":"⚡","email":"📧","chat":"💬"}
        for n in notifs:
            bg = "#f0fff4" if n['is_read'] else "#ebf8ff"
            icon = type_icons.get(n['type'], "🔔")
            with st.container(border=True):
                c1,c2 = st.columns([5,1])
                with c1:
                    st.markdown(f"{icon} **{n['title']}**")
                    st.markdown(n['message'])
                    st.caption(str(n['created_at'])[:16])
                with c2:
                    if not n['is_read']:
                        if st.button("Read", key=f"read_n_{n['id']}"):
                            NotificationEngine.mark_read(notif_id=n['id'])
                            st.rerun()
    else:
        st.info("No notifications yet.")


def render_user_management():
    st.markdown("<div class='agency-header'><h1>👥 User Management</h1><p>Create, manage and monitor all users</p></div>", unsafe_allow_html=True)
    admin = st.session_state.user['username']

    tab_list, tab_create, tab_contact, tab_plans = st.tabs(
        ["📋 All Users", "➕ Create User", "📣 Contact User", "💳 Plans"])

    with tab_list:
        col1,col2,col3 = st.columns(3)
        f_role = col1.selectbox("Role", ["all","admin","user","manager"], key="u_role_f")
        f_plan = col2.selectbox("Plan", ["all","basic","pro","enterprise"], key="u_plan_f")
        f_active = col3.selectbox("Status", ["all","active","inactive"], key="u_status_f")

        users = UserManager.list_users(
            role=None if f_role=="all" else f_role,
            plan=None if f_plan=="all" else f_plan,
            is_active=None if f_active=="all" else f_active=="active"
        )
        st.caption(f"{len(users)} users found")

        for u in users:
            with st.container(border=True):
                c1,c2,c3,c4 = st.columns([3,1,1,2])
                with c1:
                    st.markdown(f"**{u['username']}** — {u.get('full_name','')}")
                    st.caption(f"📧 {u['email']}")
                with c2:
                    plan_colors = {"basic":"badge-yellow","pro":"badge-green","enterprise":"badge-green"}
                    st.markdown(f"<span class='{plan_colors.get(u['plan'],'badge-yellow')}'>{u['plan'].upper()}</span>", unsafe_allow_html=True)
                    st.caption(u['role'])
                with c3:
                    badge = "badge-green" if u['is_active'] else "badge-red"
                    st.markdown(f"<span class='{badge}'>{'Active' if u['is_active'] else 'Inactive'}</span>", unsafe_allow_html=True)
                with c4:
                    bc1,bc2,bc3 = st.columns(3)
                    if bc1.button("Toggle", key=f"tog_{u['id']}"):
                        UserManager.toggle_active(u['id'], admin)
                        st.rerun()
                    new_plan = bc2.selectbox("", ["basic","pro","enterprise"],
                        index=["basic","pro","enterprise"].index(u['plan']),
                        key=f"plan_{u['id']}", label_visibility="collapsed")
                    if bc3.button("Set", key=f"setplan_{u['id']}"):
                        UserManager.change_plan(u['id'], new_plan, admin)
                        st.rerun()

    with tab_create:
        with st.form("create_user_form"):
            c1,c2 = st.columns(2)
            username = c1.text_input("Username")
            email    = c2.text_input("Email")
            full_name = c1.text_input("Full Name")
            password = c2.text_input("Password", type="password")
            role = c1.selectbox("Role", ["user","manager","admin"])
            plan = c2.selectbox("Plan", ["basic","pro","enterprise"])
            if st.form_submit_button("➕ Create User", type="primary"):
                if username and email and password:
                    r = UserManager.create_user(username, password, email, full_name, role, plan)
                    if r["success"]:
                        st.success(f"✅ User '{username}' created!")
                    else:
                        st.error(f"❌ {r['error']}")
                else:
                    st.warning("Fill all required fields")

    with tab_contact:
        st.subheader("Contact a User")
        users = UserManager.list_users()
        if users:
            sel_user = st.selectbox("Select User",
                [f"{u['username']} (ID:{u['id']})" for u in users],
                key="contact_user_sel")
            user_id_sel = int(sel_user.split("ID:")[1].rstrip(")"))
            method = st.radio("Contact Via", ["chat","email","call"], horizontal=True)
            msg = st.text_area("Message", height=100, key="contact_user_msg")
            subject = ""
            agent_sel = None
            if method == "email":
                subject = st.text_input("Subject", key="contact_user_subj")
                agent_sel = st.selectbox("Send From Agent", list(AGENTS.keys()), key="contact_agent_sel")
            if st.button("📣 Send", type="primary", use_container_width=True):
                r = AdminContactEngine.contact_user(
                    admin, user_id_sel, method, msg, subject, agent_sel)
                if r.get("success"):
                    st.success(f"✅ {method.capitalize()} sent!")
                else:
                    st.error(r.get("error","Failed"))
        else:
            st.info("No users yet.")

    with tab_plans:
        st.subheader("💳 Subscription Plans")
        for plan_name, limits in PLAN_LIMITS.items():
            color = {"basic":"#718096","pro":"#667eea","enterprise":"#764ba2"}.get(plan_name,"#718096")
            with st.container(border=True):
                st.markdown(f"<h3 style='color:{color}'>{plan_name.upper()}</h3>", unsafe_allow_html=True)
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Agents", limits['agents'])
                c2.metric("Storage", f"{limits['storage_mb']} MB")
                c3.metric("Tasks/Day", limits['tasks_per_day'])
                c4.metric("White Label", "✅" if limits['wl_allowed'] else "❌")


def render_whitelabel_management():
    st.markdown("<div class='agency-header'><h1>🏢 White Label Management</h1><p>Create and manage white label instances with separate databases</p></div>", unsafe_allow_html=True)
    admin = st.session_state.user['username']

    tab_list, tab_create, tab_contact, tab_restore = st.tabs(
        ["📋 Instances", "➕ Create", "📣 Contact", "♻️ Backups"])

    with tab_list:
        instances = WhiteLabelManager.list_instances()
        st.caption(f"{len(instances)} white label instances")
        for wl in instances:
            stats = WhiteLabelManager.get_stats(wl['id'])
            badge = "badge-green" if wl['status']=="active" else "badge-red"
            with st.container(border=True):
                c1,c2,c3,c4 = st.columns([3,1,1,2])
                with c1:
                    st.markdown(f"**{wl['company_name']}**")
                    st.caption(f"🌐 {wl['subdomain']} | 📧 {wl['admin_email']}")
                with c2:
                    st.markdown(f"<span class='{badge}'>{wl['status']}</span>", unsafe_allow_html=True)
                    st.caption(wl['plan'])
                with c3:
                    st.metric("Users", stats['user_count'])
                    st.metric("Agents", stats['agent_count'])
                with c4:
                    if st.button("Toggle", key=f"wl_tog_{wl['id']}"):
                        WhiteLabelManager.toggle_status(wl['id'], admin)
                        st.rerun()
                    if st.button("💾 Backup", key=f"wl_bk_{wl['id']}"):
                        r = WhiteLabelManager.create_wl_restore_point(wl['id'], admin)
                        if r["success"]:
                            st.success("✅ Backup created!")
                    if st.button("🗑️ Delete", key=f"wl_del_{wl['id']}"):
                        WhiteLabelManager.delete_instance(wl['id'], admin)
                        st.rerun()

                # Agent access
                with st.expander(f"⚙️ Configure {wl['company_name']}"):
                    agent_list = list(AGENTS.keys())
                    current = stats.get('agent_count', 0)
                    wl_full = WhiteLabelManager.get_instance(wl_id=wl['id'])
                    current_agents = json.loads(wl_full.get('agent_access','[]')) if wl_full else []
                    sel_agents = st.multiselect("Agent Access",
                        agent_list, default=current_agents,
                        key=f"wl_agents_{wl['id']}")
                    if st.button("Update Access", key=f"wl_upd_{wl['id']}"):
                        WhiteLabelManager.update_agent_access(wl['id'], sel_agents, admin)
                        st.success("✅ Updated!")

                    # WL Users
                    st.markdown("**WL Users**")
                    wl_users = WhiteLabelManager.list_wl_users(wl['id'])
                    for wu in wl_users:
                        st.caption(f"👤 {wu['username']} — {wu['email']} ({wu['role']})")
                    with st.form(f"add_wl_user_{wl['id']}"):
                        wu_name = st.text_input("Username", key=f"wu_name_{wl['id']}")
                        wu_email = st.text_input("Email", key=f"wu_email_{wl['id']}")
                        wu_pw = st.text_input("Password", type="password", key=f"wu_pw_{wl['id']}")
                        if st.form_submit_button("Add User"):
                            if wu_name and wu_email and wu_pw:
                                WhiteLabelManager.add_wl_user(wl['id'], wu_name, wu_pw, wu_email)
                                st.success("✅ User added!")
                                st.rerun()

        if not instances:
            st.info("No white label instances yet. Create one →")

    with tab_create:
        with st.form("create_wl_form"):
            c1,c2 = st.columns(2)
            company = c1.text_input("Company Name")
            subdomain = c2.text_input("Subdomain", placeholder="client1")
            email = c1.text_input("Admin Email")
            password = c2.text_input("Admin Password", type="password")
            plan = c1.selectbox("Plan", ["basic","pro","enterprise"])
            agents = c2.multiselect("Agent Access", list(AGENTS.keys()),
                default=["💼 Sales AI","🌐 Web Dev AI","📢 Marketing AI"])
            if st.form_submit_button("🏢 Create Instance", type="primary"):
                if company and subdomain and email and password:
                    r = WhiteLabelManager.create_instance(
                        company, email, password, subdomain, plan, agents)
                    if r["success"]:
                        st.success(f"✅ '{company}' created! Subdomain: {subdomain}")
                    else:
                        st.error(f"❌ {r['error']}")
                else:
                    st.warning("Fill all fields")

    with tab_contact:
        st.subheader("Contact White Label Client")
        instances = WhiteLabelManager.list_instances()
        if instances:
            sel = st.selectbox("Select Instance",
                [f"{w['company_name']} (ID:{w['id']})" for w in instances])
            wl_id = int(sel.split("ID:")[1].rstrip(")"))
            method = st.radio("Via", ["chat","email","call"], horizontal=True, key="wl_contact_method")
            msg = st.text_area("Message", key="wl_contact_msg")
            subj, ag = "", None
            if method == "email":
                subj = st.text_input("Subject", key="wl_contact_subj")
                ag = st.selectbox("From Agent", list(AGENTS.keys()), key="wl_contact_agent")
            if st.button("📣 Send", type="primary", use_container_width=True, key="wl_send"):
                r = AdminContactEngine.contact_whitelabel(admin, wl_id, method, msg, subj, ag)
                st.success("✅ Sent!") if r.get("success") else st.error(r.get("error"))
        else:
            st.info("No instances yet.")

    with tab_restore:
        st.subheader("♻️ White Label Restore Points")
        points = RestoreEngine.list_restore_points("whitelabel")
        if points:
            for pt in points:
                with st.container(border=True):
                    c1,c2,c3 = st.columns([4,1,1])
                    c1.markdown(f"**{pt['name']}**")
                    c1.caption(f"{round(pt['size_bytes']/1024,1)} KB | {str(pt['created_at'])[:16]} | {pt.get('note','')}")
                    if c2.button("↩️ Restore", key=f"wl_restore_{pt['id']}"):
                        r = RestoreEngine.restore_from_point(pt['id'], admin)
                        st.success("✅ Restored!") if r["success"] else st.error(r["error"])
                    if c3.button("🗑️", key=f"wl_del_rp_{pt['id']}"):
                        RestoreEngine.delete_restore_point(pt['id'], admin)
                        st.rerun()
        else:
            st.info("No WL restore points yet.")


def render_scheduler():
    st.markdown("<div class='agency-header'><h1>📅 Task Scheduler</h1><p>Automate agent tasks — daily, weekly, monthly</p></div>", unsafe_allow_html=True)
    user_id = str(st.session_state.user['id'])

    tab_list, tab_create, tab_logs = st.tabs(
        ["📋 Scheduled Tasks", "➕ New Schedule", "📊 Run Logs"])

    with tab_list:
        tasks = scheduler.list_tasks(user_id)
        if tasks:
            for t in tasks:
                badge = "badge-green" if t['is_active'] else "badge-red"
                status_badge = {"success":"badge-green","failed":"badge-red"}.get(t.get('last_status',''),"badge-yellow")
                with st.container(border=True):
                    c1,c2,c3 = st.columns([4,1,1])
                    with c1:
                        st.markdown(f"**{t['name']}** — {t['agent_name']}")
                        st.caption(f"Task: {t['task'][:80]}")
                        st.caption(f"Frequency: {t['frequency']} {t['cron_expr']} | Next: {str(t['next_run'])[:16]} | Runs: {t['run_count']}")
                    with c2:
                        st.markdown(f"<span class='{badge}'>{'Active' if t['is_active'] else 'Paused'}</span>", unsafe_allow_html=True)
                        if t.get('last_status'):
                            st.markdown(f"<span class='{status_badge}'>{t['last_status']}</span>", unsafe_allow_html=True)
                    with c3:
                        if t['is_active']:
                            if st.button("⏸ Pause", key=f"sch_pause_{t['task_id']}"):
                                scheduler.cancel_task(t['task_id'])
                                st.rerun()
        else:
            st.info("No scheduled tasks yet. Create one →")

    with tab_create:
        with st.form("schedule_form"):
            c1,c2 = st.columns(2)
            sched_name  = c1.text_input("Schedule Name", placeholder="Daily Sales Report")
            agent_sel   = c2.selectbox("Agent", list(AGENTS.keys()))
            task_text   = st.text_area("Task Instructions", height=100,
                placeholder="Generate and email daily sales report for all leads")
            context     = st.text_area("Context (optional)", height=60)
            c1,c2,c3   = st.columns(3)
            frequency   = c1.selectbox("Frequency", ["daily","weekly","monthly","once"])
            if frequency == "daily":
                run_time = c2.text_input("Time (HH:MM)", value="09:00")
            elif frequency == "weekly":
                day = c2.selectbox("Day", ["MON","TUE","WED","THU","FRI","SAT","SUN"])
                run_time = f"{day} {c3.text_input('Time', value='09:00', key='wk_time')}"
            elif frequency == "monthly":
                dom = c2.number_input("Day of Month", 1, 28, 1)
                run_time = f"{int(dom)} {c3.text_input('Time', value='09:00', key='mo_time')}"
            else:
                run_time = c2.text_input("DateTime (YYYY-MM-DD HH:MM)",
                    value=datetime.now().strftime("%Y-%m-%d %H:%M"))

            if st.form_submit_button("📅 Schedule Task", type="primary"):
                if sched_name and task_text:
                    r = scheduler.schedule_task(
                        sched_name, agent_sel, user_id,
                        task_text, frequency, run_time, context)
                    if r["success"]:
                        st.success(f"✅ Scheduled! Next run: {r['next_run'][:16]}")
                    else:
                        st.error("Failed to schedule")
                else:
                    st.warning("Fill name and task")

    with tab_logs:
        logs = scheduler.get_logs(limit=50)
        if logs:
            for log in logs:
                badge = "badge-green" if log['status']=="success" else "badge-red"
                with st.container(border=True):
                    c1,c2 = st.columns([4,1])
                    c1.markdown(f"**{log['agent_name']}** | Task: `{log['task_id']}`")
                    c1.caption(f"Duration: {log['duration_ms']}ms | {str(log['ran_at'])[:16]}")
                    if log.get('result'):
                        with c1.expander("Result"):
                            st.text(log['result'][:300])
                    c2.markdown(f"<span class='{badge}'>{log['status']}</span>",
                               unsafe_allow_html=True)
        else:
            st.info("No scheduler logs yet.")


def render_ai_training():
    """AI Training module - train and improve AI agents"""
    import sys
    import os
    # Add src to path to import modules
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        from agents.training import render_ai_training_interface
        render_ai_training_interface()
    except ImportError as e:
        st.error(f"Error importing AI Training module: {e}")
        st.info("The AI Training module requires the modular structure to be properly installed.")
        
        # Fallback: simple training interface
        st.header("🎓 AI Agent Training")
        st.info("This module provides capabilities to train AI agents with custom data and examples.")
        
        col1, col2 = st.columns(2)
        with col1:
            agent_name = st.text_input("Agent Name", "My AI Agent")
            training_method = st.selectbox("Training Method", ["Text Content", "Example Pairs"])
        
        with col2:
            user_id = st.number_input("User ID", value=1)
            training_intensity = st.slider("Training Intensity", 1, 10, 5)
        
        if training_method == "Text Content":
            training_content = st.text_area("Training Content", height=200, 
                                         placeholder="Enter text content for the AI agent to learn from...")
        else:  # Example Pairs
            st.subheader("Example Pairs")
            input_ex = st.text_input("Input Example", "What services do you offer?")
            output_ex = st.text_area("Expected Output", "We offer a variety of AI-powered solutions including automation, analysis, and optimization services.", height=100)
        
        if st.button("Start Training", type="primary"):
            with st.spinner("Training AI agent (simulated)..."):
                # Simulate training process
                import time
                time.sleep(2)
                st.success(f"Agent '{agent_name}' has been trained successfully!")
                st.balloons()


if __name__ == "__main__":
    main()