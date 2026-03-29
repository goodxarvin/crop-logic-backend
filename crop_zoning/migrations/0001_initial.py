from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CropArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('geometry', models.JSONField(default=dict)),
                ('points', models.JSONField(default=list)),
                ('center', models.JSONField(default=dict)),
                ('area_sqm', models.FloatField()),
                ('area_hectares', models.FloatField()),
                ('chunk_area_sqm', models.FloatField()),
                ('zone_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'crop_areas',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='CropZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('zone_id', models.CharField(max_length=64)),
                ('geometry', models.JSONField(default=dict)),
                ('points', models.JSONField(default=list)),
                ('center', models.JSONField(default=dict)),
                ('area_sqm', models.FloatField()),
                ('area_hectares', models.FloatField()),
                ('sequence', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('crop_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zones', to='crop_zoning.croparea')),
            ],
            options={
                'db_table': 'crop_zones',
                'ordering': ['sequence', 'id'],
                'constraints': [models.UniqueConstraint(fields=('crop_area', 'zone_id'), name='unique_crop_area_zone_id')],
            },
        ),
    ]
