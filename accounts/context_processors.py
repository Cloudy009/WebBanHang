# accounts/context_processors.py

def social_auth_provider(request):
    if request.user.is_authenticated:
        providers = request.user.social_auth.values_list('provider', flat=True)
        if 'google-oauth2' in providers:
            return {'auth_provider': 'google'}
        elif 'github' in providers:
            return {'auth_provider': 'github'}
    return {'auth_provider': None}
