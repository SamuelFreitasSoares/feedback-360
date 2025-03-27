from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class LoginRequiredMiddleware:
    """
    Middleware to check if a user is logged in for certain URLs.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_urls = [
            '/',                      # Login page
            '/reset-password/',       # Forgot password 
            '/admin/',                # Django admin
            '/static/',               # Static files
            '/media/',                # Media files
        ]
    
    def __call__(self, request):
        # Code to be executed before the view
        if not self._is_public_url(request.path) and 'user_type' not in request.session:
            messages.warning(request, "Você precisa estar logado para acessar esta página.")
            return redirect('login')
            
        response = self.get_response(request)
        return response
    
    def _is_public_url(self, path):
        """Check if the URL is public (no authentication required)"""
        for url in self.public_urls:
            if path.startswith(url):
                return True
        return False
