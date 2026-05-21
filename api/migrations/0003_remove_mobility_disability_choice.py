from django.db import migrations, models


def convert_mobility_to_other(apps, schema_editor):
    UserProfile = apps.get_model("api", "UserProfile")
    UserProfile.objects.filter(disability_type="mobility").update(disability_type="other")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_alertlog_building_useralertconfirmation_building"),
    ]

    operations = [
        migrations.RunPython(convert_mobility_to_other, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="disability_type",
            field=models.CharField(
                choices=[
                    ("none", "Tidak Ada"),
                    ("deaf", "Tuli / Tunarungu"),
                    ("blind", "Buta / Tunanetra"),
                    ("other", "Lainnya"),
                ],
                default="none",
                max_length=20,
            ),
        ),
    ]
