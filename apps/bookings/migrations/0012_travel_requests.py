from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('pujas', '0001_initial'),
        ('purohits', '0006_service_offers'),
        ('bookings', '0011_booking_venue_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='TravelRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_id', models.CharField(editable=False, max_length=24, unique=True)),
                ('address', models.TextField()),
                ('venue_type', models.CharField(blank=True, max_length=20)),
                ('preferred_date', models.DateField()),
                ('preferred_time', models.TimeField(blank=True, null=True)),
                ('message', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired'), ('booked', 'Booked')], default='pending', max_length=16)),
                ('travel_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('purohit_response', models.CharField(blank=True, max_length=240)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.area')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.city')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='travel_requests', to=settings.AUTH_USER_MODEL)),
                ('puja_package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pujas.purohitpujapackage')),
                ('purohit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='travel_requests', to='purohits.purohit')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='booking',
            name='travel_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='booking',
            name='travel_request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='bookings.travelrequest'),
        ),
    ]
