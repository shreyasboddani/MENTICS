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
        user_list = self.db.select("users", where={"email": self.email})
        if user_list:
            self.data = user_list[0]

    def get_name(self):
        if self.data and self.data.get('name'):
            return self.data['name']
        return "User"  # Default value

    def get_profile_picture(self):
        if self.data and self.data.get('profile_picture'):
            return self.data['profile_picture']
        return None

    def get_stats(self):
        if self.data and 'stats' in self.data:
            return json.loads(self.data['stats'])
        return {"sat": "0", "act": "0", "gpa": "0.0"}

    def set_stats(self, stats):
        if self.data:
            self.db.update("users", {"stats": json.dumps(
                stats)}, where={"email": self.email})

    @staticmethod
    def from_session(db, session):
        email = session.get("user")
        if not email:
            return None
        user = User(db, email)
        return user if user.data else None
