from functools import wraps
from django.shortcuts import redirect


def verified_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("user_login")
        if not request.user.is_verified:
            return redirect("email_verify")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
