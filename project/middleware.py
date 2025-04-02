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
            '/static/',               # Static files
            '/media/',                # Media files
            '/admin-redirect/',       # Admin redirect page
        ]
        # Django native admin should redirect to our custom admin dashboard
        self.redirect_map = {
            '/admin/': '/admin-redirect/',
            '/admin/dashboard/': '/custom-admin/dashboard/',
        }
    
    def __call__(self, request):
        # Code to be executed before the view
        path = request.path
        
        # Print debugging information about the request
        print(f"Request path: {path}")
        if 'user_type' in request.session:
            print(f"User type in session: {request.session['user_type']}")
            print(f"User ID in session: {request.session.get('user_id')}")
            print(f"Username in session: {request.session.get('username')}")
        
        # Redirect django admin urls to our custom admin
        for admin_url, redirect_url in self.redirect_map.items():
            if path.startswith(admin_url):
                print(f"Redirecting from {path} to {redirect_url}")
                return redirect(redirect_url)
            
        # Check if the path should require authentication
        if not self._is_public_url(path) and 'user_type' not in request.session:
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
