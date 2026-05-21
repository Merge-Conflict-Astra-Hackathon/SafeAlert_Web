from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_mobility_disability_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='building',
            name='floor_plan',
            field=models.ImageField(blank=True, null=True, upload_to='building_floor_plans/'),
        ),
    ]
