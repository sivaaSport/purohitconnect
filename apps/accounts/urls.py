from django.urls import path
from . import views
from . import profile_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # OTP Authentication
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('otp-verification/', views.otp_verification_view, name='otp_verification'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    
    # Phone Verification
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    path('verify-phone/otp/', views.verify_phone_otp_view, name='verify_phone_otp'),
    
    # Wallet URLs
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/topup/', views.wallet_topup, name='wallet_topup'),
    path('wallet/verify-payment/', views.verify_wallet_payment, name='verify_wallet_payment'),
    path('wallet/transactions/', views.wallet_transactions, name='wallet_transactions'),
    path('wallet/transfer/', views.wallet_transfer, name='wallet_transfer'),
    path('wallet/withdrawal/', views.wallet_withdrawal, name='wallet_withdrawal'),
    path('profile/', profile_views.profile_view, name='profile'),
    path('workspace/switch/', views.switch_workspace, name='switch_workspace'),
    
    # Razorpay Webhooks
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
]
