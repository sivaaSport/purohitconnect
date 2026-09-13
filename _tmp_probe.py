import re
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.docker")
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.purohits.models import Purohit
from apps.accounts.models import OTP

U = get_user_model()
u = U.objects.get(username="purohit_sharma")
print("phone=", u.phone, "role=", u.role, "verified=", u.is_phone_verified)

c = Client()
c.force_login(u)
for path in ["/dashboard/purohit/", "/dashboard/customer/", "/"]:
    r = c.get(path, follow=True)
    print(
        "force",
        path,
        "status",
        r.status_code,
        "redirects",
        [x[0] for x in r.redirect_chain],
        "err",
        b"Server Error" in r.content,
    )

p = Purohit.objects.filter(is_active=True).first()
print("purohit_id", p.id if p else None)
if p:
    for path in [
        f"/purohits/{p.id}/",
        f"/bookings/create/{p.id}/",
        f"/bookings/book/{p.id}/",
        f"/book/{p.id}/",
    ]:
        r = c.get(path, follow=True)
        title = re.search(br"<title>(.*?)</title>", r.content, re.S)
        t = title.group(1).decode("utf-8", "replace").strip() if title else ""
        print(
            "path",
            path,
            "status",
            r.status_code,
            "title",
            t[:70],
            "server_err",
            b"Server Error" in r.content or b"Traceback" in r.content,
            "redirects",
            [x[0] for x in r.redirect_chain],
        )

# OTP login smoke with known phone
phone = u.phone
c2 = Client()
r = c2.post("/accounts/send-otp/", {"phone": phone.replace("+91", ""), "action": "login"}, follow=True)
print("send_otp_status", r.status_code, "redirects", [x[0] for x in r.redirect_chain])
body = r.content.decode("utf-8", "replace")
for pat in ["OTP sent", "Failed to send", "Server Error", "not found", "otp"]:
    if pat.lower() in body.lower():
        print("send_otp_flag", pat)

otp = OTP.objects.filter(phone=phone).order_by("-created_at").first()
print("otp_row", bool(otp), "code", getattr(otp, "otp_code", None), "type", getattr(otp, "otp_type", None))

if otp:
    # session should have otp_phone after send; recreate by posting again then verify
    c3 = Client()
    c3.post("/accounts/send-otp/", {"phone": phone.replace("+91", ""), "action": "login"})
    otp = OTP.objects.filter(phone=phone).order_by("-created_at").first()
    r = c3.post("/accounts/verify-otp/", {"otp": otp.otp_code}, follow=True)
    print(
        "verify_otp",
        r.status_code,
        "redirects",
        [x[0] for x in r.redirect_chain],
        "logged_in",
        r.wsgi_request.user.is_authenticated if hasattr(r, "wsgi_request") else "n/a",
        "server_err",
        b"Server Error" in r.content,
    )
    title = re.search(br"<title>(.*?)</title>", r.content, re.S)
    print("verify_title", title.group(1).decode("utf-8", "replace").strip()[:80] if title else None)
