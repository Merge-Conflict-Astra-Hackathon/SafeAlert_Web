from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_building_floor_plan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="disability_type",
            field=models.CharField(
                choices=[
                    ("blind", "Tunanetra"),
                    ("deaf", "Tunarungu"),
                    ("none", "Tidak Ada"),
                    ("other", "Lainnya"),
                ],
                default="none",
                max_length=20,
            ),
        ),
    ]
