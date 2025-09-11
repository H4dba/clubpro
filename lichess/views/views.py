from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from services.LichessService import LichessApi, LichessOAuth

@login_required
def connect_lichess(request):
    oauth = LichessOAuth()
    auth_url = oauth.get_authorization_url(request)
    return redirect(auth_url)

@login_required
def lichess_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        messages.error(request, 'Authorization failed')
        return redirect('dashboard')

    oauth = LichessOAuth()
    try:
        # Exchange code for token
        token_data = oauth.exchange_code_for_token(request, code, state)
        access_token = token_data['access_token']
        
        # Initialize Lichess API with the new token
        lichess_api = LichessApi()  # Note: You might want to modify this to accept the access_token
        
        # Get user data
        user_data = lichess_api.get_user_info(request.user.username)
        
        if user_data:
            # Update user's Lichess information
            request.user.lichess_id = user_data['id']
            request.user.lichess_access_token = access_token
            request.user.is_lichess_connected = True
            
            # Update ratings if available in user_data
            if 'perfs' in user_data:
                request.user.lichess_rating_bullet = user_data['perfs'].get('bullet', {}).get('rating')
                request.user.lichess_rating_blitz = user_data['perfs'].get('blitz', {}).get('rating')
                request.user.lichess_rating_rapid = user_data['perfs'].get('rapid', {}).get('rating')
                request.user.lichess_rating_classical = user_data['perfs'].get('classical', {}).get('rating')
            
            request.user.save()
            messages.success(request, 'Successfully connected to Lichess!')
        else:
            messages.error(request, 'Failed to fetch Lichess user data')
            
    except Exception as e:
        messages.error(request, f'Failed to connect to Lichess: {str(e)}')

    return redirect('dashboard')


