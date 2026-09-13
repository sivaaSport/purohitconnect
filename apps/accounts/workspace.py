"""One account can hold two workspaces: devotee and purohit.

`CustomUser.role` stays the signup default. Active workspace lives in the
session so navbar, home, and dashboards stay consistent without a second login.
"""
from django.urls import reverse

WORKSPACE_SESSION_KEY = 'active_workspace'
DEVOTEE = 'devotee'
PUROHIT = 'purohit'


def can_act_as_devotee(user) -> bool:
    return bool(user and getattr(user, 'is_authenticated', False))


def can_act_as_purohit(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if hasattr(user, 'can_act_as_purohit'):
        return bool(user.can_act_as_purohit())
    return getattr(user, 'role', '') == 'purohit'


def has_dual_workspace(user) -> bool:
    return can_act_as_devotee(user) and can_act_as_purohit(user)


def get_active_workspace(request) -> str:
    user = getattr(request, 'user', None)
    if not can_act_as_devotee(user):
        return DEVOTEE
    stored = request.session.get(WORKSPACE_SESSION_KEY)
    if stored == PUROHIT and can_act_as_purohit(user):
        return PUROHIT
    if stored == DEVOTEE:
        return DEVOTEE
    return PUROHIT if getattr(user, 'role', '') == 'purohit' else DEVOTEE


def set_active_workspace(request, workspace: str) -> str:
    if workspace == PUROHIT and can_act_as_purohit(request.user):
        request.session[WORKSPACE_SESSION_KEY] = PUROHIT
        return PUROHIT
    request.session[WORKSPACE_SESSION_KEY] = DEVOTEE
    return DEVOTEE


def workspace_home_name(request) -> str:
    return 'dashboard:purohit' if get_active_workspace(request) == PUROHIT else 'dashboard:customer'


def enable_purohit_workspace(user):
    """Give a devotee a purohit listing so they can switch workspaces."""
    from apps.accounts.models import CustomerProfile, PurohitProfile
    from apps.purohits.services import ensure_purohit_listing

    CustomerProfile.objects.get_or_create(user=user)
    PurohitProfile.objects.get_or_create(user=user)
    if user.role != 'purohit':
        user.role = 'purohit'
        user.save(update_fields=['role'])
    return ensure_purohit_listing(user)


def ensure_devotee_profile(user):
    from apps.accounts.models import CustomerProfile
    CustomerProfile.objects.get_or_create(user=user)
    return user
