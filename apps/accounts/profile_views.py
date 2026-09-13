"""Profile and gallery management views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.models import CustomerProfile, PurohitProfile
from apps.core.models import City, Language
from apps.purohits.models import PurohitMedia
from apps.purohits.services import ensure_purohit_listing


@login_required
def profile_view(request):
    """View and edit the logged-in user profile, avatar, and purohit gallery."""
    user = request.user
    purohit = None
    gallery = []
    CustomerProfile.objects.get_or_create(user=user)
    if user.can_act_as_purohit():
        purohit = ensure_purohit_listing(user)
        if purohit:
            gallery = list(purohit.gallery_media.all()[:36])
        PurohitProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        action = (request.POST.get('action') or 'save_profile').strip()

        if action == 'save_profile':
            user.first_name = (request.POST.get('first_name') or '').strip()[:150]
            user.last_name = (request.POST.get('last_name') or '').strip()[:150]
            city_id = request.POST.get('city')
            if city_id:
                city = City.objects.filter(id=city_id).first()
                if city:
                    user.city = city
            avatar = request.FILES.get('avatar')
            if avatar:
                if avatar.size > 5 * 1024 * 1024:
                    messages.error(request, 'Profile photo must be under 5 MB.')
                    return redirect('accounts:profile')
                content_type = (avatar.content_type or '').lower()
                if not content_type.startswith('image/'):
                    messages.error(request, 'Profile photo must be an image file.')
                    return redirect('accounts:profile')
                user.avatar = avatar
            user.save()

            if user.can_act_as_purohit() and purohit:
                display_name = (request.POST.get('display_name') or '').strip()[:200]
                if display_name:
                    purohit.name = display_name
                    purohit.save(update_fields=['name', 'updated_at'])
                profile = user.purohit_profile
                try:
                    profile.experience_years = max(0, int(request.POST.get('experience_years') or 0))
                except (TypeError, ValueError):
                    profile.experience_years = 0
                profile.about = (request.POST.get('about') or '').strip()
                profile.save()
                lang_ids = request.POST.getlist('languages')
                profile.languages_spoken.set(Language.objects.filter(id__in=lang_ids))

            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')

        if action == 'remove_avatar':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
                messages.success(request, 'Profile photo removed.')
            return redirect('accounts:profile')

        if action == 'upload_gallery' and user.can_act_as_purohit() and purohit:
            upload = request.FILES.get('media_file')
            if not upload:
                messages.error(request, 'Choose a photo or video to upload.')
                return redirect('accounts:profile')
            content_type = (upload.content_type or '').lower()
            if content_type.startswith('image/'):
                media_type = 'photo'
                if upload.size > 8 * 1024 * 1024:
                    messages.error(request, 'Gallery photos must be under 8 MB.')
                    return redirect('accounts:profile')
            elif content_type.startswith('video/'):
                media_type = 'video'
                if upload.size > 40 * 1024 * 1024:
                    messages.error(request, 'Gallery videos must be under 40 MB.')
                    return redirect('accounts:profile')
            else:
                messages.error(request, 'Only image or video files are supported.')
                return redirect('accounts:profile')

            if purohit.gallery_media.count() >= 36:
                messages.error(request, 'Gallery limit reached (36 items). Remove some to add more.')
                return redirect('accounts:profile')

            PurohitMedia.objects.create(
                purohit=purohit,
                media_type=media_type,
                file=upload,
                title=(request.POST.get('title') or '').strip()[:120],
                caption=(request.POST.get('caption') or '').strip()[:255],
                is_featured=request.POST.get('is_featured') == 'on',
            )
            messages.success(request, 'Gallery item added.')
            return redirect('accounts:profile')

        if action == 'delete_gallery' and user.can_act_as_purohit() and purohit:
            item = PurohitMedia.objects.filter(
                id=request.POST.get('media_id'), purohit=purohit
            ).first()
            if item:
                item.file.delete(save=False)
                item.delete()
                messages.success(request, 'Gallery item removed.')
            return redirect('accounts:profile')

        if action == 'toggle_featured' and user.can_act_as_purohit() and purohit:
            item = PurohitMedia.objects.filter(
                id=request.POST.get('media_id'), purohit=purohit
            ).first()
            if item:
                item.is_featured = not item.is_featured
                item.save(update_fields=['is_featured'])
            return redirect('accounts:profile')

    selected_language_ids = []
    if user.can_act_as_purohit() and hasattr(user, 'purohit_profile'):
        selected_language_ids = list(
            user.purohit_profile.languages_spoken.values_list('id', flat=True)
        )

    context = {
        'profile_user': user,
        'purohit': purohit,
        'gallery': gallery,
        'cities': City.objects.all().order_by('name'),
        'languages': Language.objects.all().order_by('name'),
        'selected_language_ids': selected_language_ids,
    }
    return render(request, 'accounts/profile.html', context)
