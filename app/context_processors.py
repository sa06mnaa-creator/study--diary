from .models import Profile

def header_profile(request):
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return{"header_profile": profile}
    return {"header_profile": None}