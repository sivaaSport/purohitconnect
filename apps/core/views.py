from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Notification

def home(request):
    """Landing page. Purohit workspace lands on the provider dashboard."""
    if request.user.is_authenticated:
        from apps.accounts.workspace import PUROHIT, get_active_workspace
        if get_active_workspace(request) == PUROHIT:
            return redirect('dashboard:purohit')
    return render(request, 'pages/home.html')

def about(request):
    """Render the about page."""
    return render(request, 'pages/about.html')

def support_center(request):
    """Render the support center / help page."""
    return render(request, 'pages/about.html')

@login_required
def create_ticket(request):
    """Create a support ServiceRequest from the support bot / form."""
    from .models import ServiceRequest

    if request.method != 'POST':
        return redirect('core:support')

    subject = (request.POST.get('subject') or '').strip()
    description = (request.POST.get('description') or '').strip()
    category = (request.POST.get('category') or 'general').strip() or 'general'

    valid_categories = {'general', 'booking', 'payment', 'technical', 'purohit_verification'}
    if category not in valid_categories:
        category = 'general'

    # HTMX-friendly validation errors
    if not subject or not description:
        html = (
            '<div style="padding:1rem;color:#FCA5A5;">'
            'Please provide both a subject and description.'
            '</div>'
            '<div style="margin-top:0.75rem;">'
            '<button type="button" onclick="window.location.reload()" class="btn btn-outline" style="width:100%;">'
            'Try Again</button></div>'
        )
        if request.htmx:
            return HttpResponse(html, status=400)
        messages.error(request, "Please provide both a subject and description.")
        return redirect('core:support')

    priority = 'medium'
    if category in {'payment', 'technical'}:
        priority = 'high'
    elif category == 'general':
        priority = 'low'

    ticket = ServiceRequest.objects.create(
        user=request.user,
        subject=subject[:200],
        description=description,
        category=category,
        priority=priority,
        status='open',
    )

    # Notify staff users (best-effort)
    from apps.accounts.models import CustomUser
    staff_users = CustomUser.objects.filter(is_staff=True, is_active=True)[:10]
    for staff in staff_users:
        Notification.objects.create(
            user=staff,
            title='New Support Ticket',
            message=f'{ticket.ticket_id}: {ticket.subject}',
            link='/dashboard/admin/support/'
        )

    success_html = f'''
        <div style="display:flex; gap:0.5rem; margin-bottom:1rem;">
            <div style="width:28px;height:28px;border-radius:50%;background:rgba(16,185,129,0.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <i data-lucide="check" style="width:14px;height:14px;color:#10B981;"></i>
            </div>
            <div style="background:rgba(16,185,129,0.12);color:var(--color-text-main);padding:0.75rem;border-radius:0 12px 12px 12px;font-size:0.9rem;line-height:1.4;">
                Thanks! Your request <strong>{ticket.ticket_id}</strong> has been created.
                Our team will get back to you shortly.
            </div>
        </div>
        <button type="button" onclick="window.location.reload()" class="btn btn-outline" style="width:100%;">
            Raise Another Request
        </button>
        <script>if (window.lucide) lucide.createIcons();</script>
    '''

    if request.htmx:
        return HttpResponse(success_html)

    messages.success(request, f"Support ticket {ticket.ticket_id} created successfully.")
    return redirect('core:support')

@login_required
def get_notifications_count(request):
    """Return the count of unread notifications for the current user."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def get_notifications_list(request):
    """Return the list of notifications for the current user."""
    notifications = request.user.notifications.all()[:20]
    return render(request, 'components/partials/notification_list.html', {'notifications': notifications})

@login_required
def mark_notifications_read(request):
    """Mark all notifications for the user as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return HttpResponse(status=204) # No content response for HTMX

@login_required
def mark_single_notification_read(request, pk):
    """Mark a specific notification as read and redirect if it has a link."""
    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('HX-Request'):
        notifications = request.user.notifications.all()[:20]
        return render(request, 'components/partials/notification_list.html', {'notifications': notifications})
    
    if notification.link:
        return redirect(notification.link)
    return redirect('core:home')

@login_required
def delete_single_notification(request, pk):
    """Delete a specific notification."""
    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.delete()
    
    if request.headers.get('HX-Request'):
        notifications = request.user.notifications.all()[:20]
        return render(request, 'components/partials/notification_list.html', {'notifications': notifications})
    
    return redirect('core:home')

@login_required
def clear_all_notifications(request):
    """Delete all notifications for the current user."""
    request.user.notifications.all().delete()
    messages.success(request, "All notifications cleared.")
    from apps.accounts.workspace import workspace_home_name
    return redirect(workspace_home_name(request))
