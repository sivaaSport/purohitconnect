from datetime import time

from django.db import migrations, models


def backfill_package_durations(apps, schema_editor):
    Package = apps.get_model('pujas', 'PurohitPujaPackage')
    for package in Package.objects.select_related('puja').iterator():
        if package.duration_hours is None and package.puja_id:
            package.duration_hours = package.puja.base_duration_hours
            package.save(update_fields=['duration_hours'])


class Migration(migrations.Migration):

    dependencies = [
        ('pujas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purohitpujapackage',
            name='duration_hours',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='How long this purohit needs for this ritual (hours).',
                max_digits=4,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='purohitpujapackage',
            name='buffer_minutes',
            field=models.PositiveSmallIntegerField(
                default=30,
                help_text='Soft cushion after the ritual before the next booking can start.',
            ),
        ),
        migrations.AlterField(
            model_name='puja',
            name='base_duration_hours',
            field=models.DecimalField(
                decimal_places=2,
                help_text='Suggested typical duration. Each purohit sets their real duration on their package.',
                max_digits=4,
            ),
        ),
        migrations.RunPython(backfill_package_durations, migrations.RunPython.noop),
    ]
