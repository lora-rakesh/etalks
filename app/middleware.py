# middleware.py
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import redirect

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        now = datetime.now()
        last_activity = request.session.get('last_activity')

        if last_activity:
            elapsed = now - datetime.fromisoformat(last_activity)
            if elapsed > timedelta(seconds=300):  # 5 minutes
                from django.contrib.auth import logout
                logout(request)
                return redirect('index')  # Replace with your login URL name

        request.session['last_activity'] = now.isoformat()
        return self.get_response(request)
