from django.db import migrations, models
import django.db.models.deletion


def copy_service_areas_to_offers(apps, schema_editor):
    Purohit = apps.get_model('purohits', 'Purohit')
    Offer = apps.get_model('purohits', 'PurohitServiceOffer')
    for purohit in Purohit.objects.all():
        areas = list(purohit.service_areas.all())
        if areas:
            for area in areas:
                Offer.objects.get_or_create(
                    purohit=purohit,
                    city_id=area.city_id,
                    area=area,
                    kind='permanent',
                    defaults={'is_active': True},
                )
        elif purohit.city_id:
            Offer.objects.get_or_create(
                purohit=purohit,
                city_id=purohit.city_id,
                area_id=purohit.base_area_id,
                kind='permanent',
                defaults={'is_active': True},
            )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('purohits', '0005_purohit_travel_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='purohit',
            name='accepts_travel_requests',
            field=models.BooleanField(
                default=True,
                help_text='Allow devotees to request a visit when you do not already offer their location.',
            ),
        ),
        migrations.CreateModel(
            name='PurohitServiceOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('permanent', 'Permanent'), ('visit', 'Temporary visit')], default='permanent', max_length=16)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=240)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purohit_service_offers', to='core.area')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purohit_service_offers', to='core.city')),
                ('purohit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_offers', to='purohits.purohit')),
            ],
            options={
                'ordering': ['kind', 'city__name', 'area__name', '-start_date'],
            },
        ),
        migrations.RunPython(copy_service_areas_to_offers, migrations.RunPython.noop),
    ]
