from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.bookings.models import Booking
from apps.purohits.models import Purohit
from .models import Review

@login_required(login_url='accounts:login')
def write_review(request, booking_id):
    """View to write a review for a completed booking."""
    booking = get_object_or_404(Booking.objects.select_related('purohit', 'customer'), booking_id=booking_id)
    customer = request.user
    booking = get_object_or_404(Booking, booking_id=booking_id, customer=customer)
        
    if booking.status != 'completed':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Ritual not completed'}, status=400)
        messages.error(request, "You can only review completed pujas.")
        return redirect('/')
        
    review = getattr(booking, 'review', None)
        
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        title = request.POST.get('title', 'Review')
        comment = request.POST.get('comment')
        
        if review:
            review.rating = rating
            review.title = title
            review.comment = comment
            review.save()
            msg = "Review updated successfully!"
        else:
            Review.objects.create(
                reviewer=customer,
                purohit=booking.purohit,
                booking=booking,
                rating=rating,
                title=title,
                comment=comment
            )
            msg = "Thank you for your review!"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'message': msg})
            
        messages.success(request, msg)
        return redirect('dashboard:customer')
        
    context = {
        'booking': booking
    }
    return render(request, 'reviews/write_review.html', context)
