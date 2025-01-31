# Generated by Django 5.1.4 on 2024-12-15 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mailing", "0003_attempt_recipient_alter_attempt_newsletter_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsletter",
            name="status",
            field=models.CharField(
                choices=[
                    ("Создана", "Создана"),
                    ("Запущена", "Запущена"),
                    ("Приостановлена", "Приостановлена"),
                    ("Завершена", "Завершена"),
                ],
                default="Создана",
                max_length=15,
            ),
        ),
    ]
