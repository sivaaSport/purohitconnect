# Generated for purohit gallery media

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('purohits', '0002_timed_availability'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurohitMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_type', models.CharField(choices=[('photo', 'Photo'), ('video', 'Video')], default='photo', max_length=10)),
                ('file', models.FileField(upload_to='purohit_gallery/%Y/%m/')),
                ('title', models.CharField(blank=True, max_length=120)),
                ('caption', models.CharField(blank=True, max_length=255)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('purohit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_media', to='purohits.purohit')),
            ],
            options={
                'verbose_name_plural': 'Purohit gallery media',
                'ordering': ['-is_featured', '-created_at'],
            },
        ),
    ]
