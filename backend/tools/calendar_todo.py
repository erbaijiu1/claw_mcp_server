import os
import uuid
import json
import pymysql
from datetime import datetime, timedelta

# Database Configuration
DB_HOST = os.environ.get("DB_HOST", "host.docker.internal")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Gmcc@123")
DB_NAME = os.environ.get("DB_NAME", "openclaw_mcp")

def get_connection(db_name=DB_NAME):
    """Establishes a connection to the MySQL database."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    """Initialize the database and tables if they do not exist."""
    # Connect without specifying database to create it if necessary
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    finally:
        conn.close()

    # Connect to the specific database to create tables
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Table: tasks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(50) DEFAULT 'WORK',
                    tags JSON,
                    priority VARCHAR(50),
                    status VARCHAR(50),
                    due_date DATE,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            
            # Table: task_history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_id VARCHAR(36),
                    action VARCHAR(50),
                    old_value TEXT,
                    new_value TEXT,
                    changed_at DATETIME,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            """)
        conn.commit()
    finally:
        conn.close()

# Ensure DB is initialized when module loads
try:
    init_db()
except Exception as e:
    print(f"Failed to initialize database: {e}")


def get_daily_briefing(date_str: str = None) -> dict:
    """
    Get a daily briefing of tasks, including overdue, today's, and high-priority tasks.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Overdue tasks (due date < date_str and not done/cancelled)
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE due_date < %s AND status NOT IN ('DONE', 'CANCELLED')
            """, (date_str,))
            overdue_tasks = cursor.fetchall()
            
            # Today's tasks
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE due_date = %s AND status NOT IN ('DONE', 'CANCELLED')
            """, (date_str,))
            today_tasks = cursor.fetchall()
            
            # High priority tasks (P0 or P1)
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE priority IN ('P0-紧急', 'P1-高') AND status NOT IN ('DONE', 'CANCELLED')
            """, ())
            high_priority_tasks = cursor.fetchall()
            
            # Helper to convert dates to string
            def format_tasks(task_list):
                for task in task_list:
                    if task.get('due_date'):
                        task['due_date'] = str(task['due_date'])
                    if task.get('created_at'):
                        task['created_at'] = str(task['created_at'])
                    if task.get('updated_at'):
                        task['updated_at'] = str(task['updated_at'])
                return task_list
                
            return {
                "date": date_str,
                "overdue_tasks": format_tasks(overdue_tasks),
                "today_tasks": format_tasks(today_tasks),
                "high_priority_tasks": format_tasks(high_priority_tasks)
            }
    finally:
        conn.close()

def get_next_n_days_briefing(date_str: str = None, days: int = 7) -> dict:
    """
    Get a briefing of tasks for the next N days, including overdue, upcoming N days, and high-priority tasks.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    end_date = start_date + timedelta(days=max(0, days - 1))
    end_date_str = end_date.strftime("%Y-%m-%d")
        
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Overdue tasks (due date < date_str and not done/cancelled)
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE due_date < %s AND status NOT IN ('DONE', 'CANCELLED')
            """, (date_str,))
            overdue_tasks = cursor.fetchall()
            
            # Next N days' tasks
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE due_date >= %s AND due_date <= %s AND status NOT IN ('DONE', 'CANCELLED')
                ORDER BY due_date ASC
            """, (date_str, end_date_str))
            upcoming_tasks = cursor.fetchall()
            
            # High priority tasks (P0 or P1)
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE priority IN ('P0-紧急', 'P1-高') AND status NOT IN ('DONE', 'CANCELLED')
            """, ())
            high_priority_tasks = cursor.fetchall()
            
            # Helper to convert dates to string
            def format_tasks(task_list):
                for task in task_list:
                    if task.get('due_date'):
                        task['due_date'] = str(task['due_date'])
                    if task.get('created_at'):
                        task['created_at'] = str(task['created_at'])
                    if task.get('updated_at'):
                        task['updated_at'] = str(task['updated_at'])
                return task_list
                
            return {
                "start_date": date_str,
                "end_date": end_date_str,
                "days": days,
                "overdue_tasks": format_tasks(overdue_tasks),
                "upcoming_tasks": format_tasks(upcoming_tasks),
                "high_priority_tasks": format_tasks(high_priority_tasks)
            }
    finally:
        conn.close()

def create_task(title: str, description: str = None, due_date: str = None, priority: str = 'P2-中', category: str = 'WORK', tags: list = None) -> dict:
    """
    Create a new task and log the action.
    """
    task_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "TODO"
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Insert Task
            cursor.execute("""
                INSERT INTO tasks (id, title, description, category, tags, priority, status, due_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (task_id, title, description, category, tags_json, priority, status, due_date, now, now))
            
            # Insert History
            new_value = json.dumps({
                "title": title,
                "description": description,
                "category": category,
                "tags": tags,
                "priority": priority,
                "status": status,
                "due_date": due_date
            }, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO task_history (task_id, action, old_value, new_value, changed_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (task_id, 'CREATE', None, new_value, now))
            
        conn.commit()
        return {"id": task_id, "status": "success", "message": f"Task '{title}' created successfully."}
    finally:
        conn.close()

def update_task(task_id: str, status: str = None, due_date: str = None, priority: str = None, title: str = None, description: str = None, category: str = None, tags: list = None) -> dict:
    """
    Update an existing task and log the changes.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch existing task
            cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            old_task = cursor.fetchone()
            
            if not old_task:
                return {"status": "error", "message": f"Task with id {task_id} not found."}
                
            updates = []
            params = []
            old_val_dict = {}
            new_val_dict = {}
            
            def check_and_update(field_name, new_val):
                old_val = old_task[field_name]
                if isinstance(old_val, datetime) or hasattr(old_val, 'isoformat'): # Handle dates
                    old_val_str = str(old_val)
                else:
                    old_val_str = old_val
                    
                if new_val is not None and new_val != old_val_str:
                    updates.append(f"{field_name} = %s")
                    params.append(new_val)
                    old_val_dict[field_name] = old_val_str
                    new_val_dict[field_name] = new_val
                    
            check_and_update('title', title)
            check_and_update('description', description)
            check_and_update('category', category)
            check_and_update('status', status)
            check_and_update('due_date', due_date)
            check_and_update('priority', priority)
            
            if tags is not None:
                # tags requires special handling for JSON string matching
                tags_json = json.dumps(tags, ensure_ascii=False)
                if not old_task['tags'] or old_task['tags'] != tags_json:
                    updates.append("tags = %s")
                    params.append(tags_json)
                    old_val_dict['tags'] = old_task['tags']
                    new_val_dict['tags'] = tags
            
            if not updates:
                return {"status": "success", "message": "No fields to update."}
                
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updates.append("updated_at = %s")
            params.append(now)
            params.append(task_id)
            
            update_query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(update_query, tuple(params))
            
            # Insert History
            action = "DELAY" if due_date else "UPDATE"
            if status and status == 'DONE':
                action = "COMPLETE"
                
            cursor.execute("""
                INSERT INTO task_history (task_id, action, old_value, new_value, changed_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (task_id, action, json.dumps(old_val_dict, ensure_ascii=False), json.dumps(new_val_dict, ensure_ascii=False), now))
            
        conn.commit()
        return {"status": "success", "message": f"Task {task_id} updated successfully."}
    finally:
        conn.close()

def query_tasks(status: str = None, priority: str = None, category: str = None, tag: str = None, keyword: str = None, is_overdue: bool = None) -> list:
    """
    Query tasks based on multiple conditions.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
            if priority:
                query += " AND priority = %s"
                params.append(priority)
            if category:
                query += " AND category = %s"
                params.append(category)
            if tag:
                query += " AND JSON_CONTAINS(tags, %s)"
                params.append(f'"{tag}"')
            if keyword:
                query += " AND (title LIKE %s OR description LIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if is_overdue:
                date_str = datetime.now().strftime("%Y-%m-%d")
                query += " AND due_date < %s AND status NOT IN ('DONE', 'CANCELLED')"
                params.append(date_str)
                
            query += " ORDER BY due_date ASC, priority ASC"
            
            cursor.execute(query, tuple(params))
            tasks = cursor.fetchall()
            
            # Format dates
            for task in tasks:
                if task.get('due_date'):
                    task['due_date'] = str(task['due_date'])
                if task.get('created_at'):
                    task['created_at'] = str(task['created_at'])
                if task.get('updated_at'):
                    task['updated_at'] = str(task['updated_at'])
            return tasks
    finally:
        conn.close()

def get_task_history(task_id: str) -> list:
    """
    Retrieve the modification history for a specific task.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM task_history WHERE task_id = %s ORDER BY changed_at DESC", (task_id,))
            history = cursor.fetchall()
            
            for record in history:
                if record.get('changed_at'):
                    record['changed_at'] = str(record['changed_at'])
            return history
    finally:
        conn.close()
