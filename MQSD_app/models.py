from flask_login import UserMixin
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, user_data):
        self._id = str(user_data.get('_id'))
        self._email = user_data.get('email')
        self.password_hash = user_data.get('password')
        self._full_name = user_data.get('full_name')
        self._location = user_data.get('location')
        self._preferred_cities = user_data.get('preferred_cities', [])
        self._interests = user_data.get('interests', [])
        self._languages = user_data.get('languages', [])
        self.header_image = user_data.get('header_image')  # Base64 encoded image
        self.profile_theme = user_data.get('profile_theme', 'default')  # Theme selection

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self._id

    @property
    def id(self):
        return self._id

    @property
    def email(self):
        return self._email

    @property
    def full_name(self):
        return self._full_name

    @property
    def location(self):
        return self._location

    @property
    def preferred_cities(self):
        return self._preferred_cities

    @property
    def interests(self):
        return self._interests

    @property
    def languages(self):
        return self._languages

    @property
    def trips(self):
        return self.user_data.get('trips', []) 