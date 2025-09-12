# validators.py

import re
from django.core.exceptions import ValidationError

class StrongPasswordValidator:
    def __init__(self):
        self.min_length = 8
        self.special_characters = r'[@#$%^&+=]'
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError("Password must be at least 8 characters long.")

        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")

        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(self.special_characters, password):
            raise ValidationError("Password must contain at least one special character (e.g. @, #, $, %, ^, &).")
        
        if user:
            if user.username in password:
                raise ValidationError("Password cannot contain your username.")
            if user.employee_id in password:
                raise ValidationError("Password cannot contain your employee ID.")

    def get_help_text(self):
        return ("Your password must be at least 8 characters long, "
                "contain at least one uppercase letter, one lowercase letter, "
                "one special character (@, #, $, %, ^, &, +), and cannot contain your username or employee ID.")
