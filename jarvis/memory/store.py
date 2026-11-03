import sqlite3
from datetime import datetime
class MemoryStore:
    def __init__(self,database):
        database.parent.mkdir(parents=True,exist_ok=True); self.db=sqlite3.connect(database,check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY, kind TEXT, content TEXT, created_at TEXT)"); self.db.execute("CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, content TEXT, due_at TEXT, completed INTEGER DEFAULT 0)"); self.db.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, timestamp TEXT, tool TEXT, action TEXT, risk TEXT, approved INTEGER, result TEXT)"); self.db.commit()
    def remember(self,content,kind="long_term"): self.db.execute("INSERT INTO memories(kind,content,created_at) VALUES(?,?,?)",(kind,content,datetime.now().isoformat())); self.db.commit()
    def memories(self,limit=20): return self.db.execute("SELECT id,kind,content,created_at FROM memories ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    def forget(self,ident): self.db.execute("DELETE FROM memories WHERE id=?",(ident,)); self.db.commit()
    def add_reminder(self,content,due_at): self.db.execute("INSERT INTO reminders(content,due_at) VALUES(?,?)",(content,due_at)); self.db.commit()
    def audit(self,tool,action,risk,approved,result): self.db.execute("INSERT INTO audit(timestamp,tool,action,risk,approved,result) VALUES(?,?,?,?,?,?)",(datetime.now().isoformat(),tool,action,risk,bool(approved),result[:1000]));self.db.commit()
