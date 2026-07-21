import os
import unittest
from datetime import datetime
import pymysql

# Set environment variables for testing (overriding if necessary)
# Normally these would be set via docker-compose or environment
if 'DB_HOST' not in os.environ:
    os.environ['DB_HOST'] = 'mysql_db'
if 'DB_USER' not in os.environ:
    os.environ['DB_USER'] = 'root'
if 'DB_PASSWORD' not in os.environ:
    os.environ['DB_PASSWORD'] = 'Gmcc@123'
if 'DB_NAME' not in os.environ:
    os.environ['DB_NAME'] = 'openclaw_mcp'

# Import tools after setting environ
from tools.calendar_todo import (
    get_daily_briefing,
    create_task,
    update_task,
    query_tasks,
    get_task_history,
    init_db,
    get_connection
)

class TestCalendarTodo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database is initialized
        init_db()
        
    def setUp(self):
        # Clean up tasks table before each test
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tasks")
            conn.commit()
        finally:
            conn.close()

    def test_create_and_query_task(self):
        # Create a task
        res = create_task(title="Test Task", description="This is a test", due_date="2026-12-31", priority="P1-高", category="LIFE", tags=["旅行", "重要"])
        self.assertEqual(res['status'], 'success')
        task_id = res['id']
        
        # Query task by tag
        tasks = query_tasks(tag="旅行")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['category'], "LIFE")
        import json
        self.assertEqual(json.loads(tasks[0]['tags']), ["旅行", "重要"])
        
        # Check history
        history = get_task_history(task_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['action'], 'CREATE')
        
    def test_update_task(self):
        res = create_task(title="Task to update", due_date="2026-12-31", category="WORK", tags=["会议"])
        task_id = res['id']
        
        update_res = update_task(task_id, status="DONE", priority="P0-紧急", category="STUDY", tags=["会议", "结束"])
        self.assertEqual(update_res['status'], 'success')
        
        tasks = query_tasks(status="DONE")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['priority'], "P0-紧急")
        self.assertEqual(tasks[0]['category'], "STUDY")
        
        history = get_task_history(task_id)
        self.assertEqual(len(history), 2)
        
    def test_daily_briefing(self):
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Overdue
        create_task(title="Overdue Task", due_date="2020-01-01")
        # Today
        create_task(title="Today Task", due_date=today)
        # High priority but future
        create_task(title="High Priority Future", due_date="2030-01-01", priority="P0-紧急")
        
        briefing = get_daily_briefing(today)
        
        self.assertEqual(len(briefing['overdue_tasks']), 1)
        self.assertEqual(briefing['overdue_tasks'][0]['title'], "Overdue Task")
        
        self.assertEqual(len(briefing['today_tasks']), 1)
        self.assertEqual(briefing['today_tasks'][0]['title'], "Today Task")
        
        self.assertEqual(len(briefing['high_priority_tasks']), 1)
        self.assertEqual(briefing['high_priority_tasks'][0]['title'], "High Priority Future")

if __name__ == '__main__':
    unittest.main()
