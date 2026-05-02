from django.db import migrations, models


PENDING_STATUS = "pending_confirmation"
OLD_STATUSES = {"", "success", "error", None}


def migrate_existing_statuses(apps, schema_editor):
    Recommendation = apps.get_model("fertilization_recommendation", "FertilizationRecommendationRequest")
    Recommendation.objects.filter(status__in=[status for status in OLD_STATUSES if status is not None]).update(
        status=PENDING_STATUS
    )
    Recommendation.objects.filter(status__isnull=True).update(status=PENDING_STATUS)


class Migration(migrations.Migration):
    dependencies = [
        ("fertilization_recommendation", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fertilizationrecommendationrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("in_progress", "در حال مصرف"),
                    ("pending_confirmation", "منتظر تایید"),
                    ("completed", "پایان یافته"),
                ],
                db_index=True,
                default="pending_confirmation",
                max_length=64,
            ),
        ),
        migrations.RunPython(migrate_existing_statuses, migrations.RunPython.noop),
    ]
