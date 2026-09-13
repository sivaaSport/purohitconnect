from django.conf import settings

from apps.accounts.workspace import (
    can_act_as_purohit,
    get_active_workspace,
    has_dual_workspace,
)


def global_settings(request):
    """
    Context processor to pass global variables to all templates.
    """
    user = getattr(request, 'user', None)
    authenticated = bool(user and getattr(user, 'is_authenticated', False))
    workspace = get_active_workspace(request) if authenticated else 'devotee'
    return {
        'SITE_NAME': 'PurohitConnect',
        'SITE_DOMAIN': 'purohitconnect.in',
        'active_workspace': workspace,
        'is_purohit_workspace': workspace == 'purohit',
        'is_devotee_workspace': workspace == 'devotee',
        'can_switch_to_purohit': authenticated and can_act_as_purohit(user),
        'has_dual_workspace': authenticated and has_dual_workspace(user),
    }
