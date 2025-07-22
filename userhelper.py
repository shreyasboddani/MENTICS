# userhelper.py
import json

class User:
    def __init__(self, db, email=None):
        self.db = db
        self.email = email
        self.data = None
        if email:
            self.load_user()

    def load_user(self):
        user = self.db.select("users", where={"email": self.email})
        if user:
            self.data = user[0]

    def get_stats(self):
        if self.data and len(self.data) >= 4:
            return json.loads(self.data[3])
        return {"sat": "0", "act": "0", "gpa": "0.0"}

    def set_stats(self, stats):
        if self.data:
            self.db.update("users", {"stats": json.dumps(stats)}, where={"email": self.email})

    @staticmethod
    def from_session(db, session):
        email = session.get("user")
        if not email:
            return None
        user = User(db, email)
        return user if user.data else None
