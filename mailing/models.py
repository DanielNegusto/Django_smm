from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.conf import settings


class Recipient(models.Model):
    email = models.EmailField(unique=False)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)

    class Meta:
        permissions = [
            ('can_view_recipient', 'Can view recipient'),
            ('can_edit_recipient', 'Can edit recipient'),
            ('can_delete_recipient', 'Can delete recipient'),
        ]

    def __str__(self):
        return self.full_name


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)

    class Meta:
        permissions = [
            ('can_view_message', 'Can view message'),
            ('can_edit_message', 'Can edit message'),
            ('can_delete_message', 'Can delete message'),
        ]

    def __str__(self):
        return self.subject


class Newsletter(models.Model):
    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Приостановлена', 'Приостановлена'),  # Новый статус
        ('Завершена', 'Завершена'),
    ]

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Создана')  # Увеличен max_length для нового статуса
    message = models.ForeignKey('Message', on_delete=models.CASCADE)
    recipients = models.ManyToManyField('Recipient')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)

    class Meta:
        permissions = [
            ('can_view_newsletter', 'Can view newsletter'),
            ('can_edit_newsletter', 'Can edit newsletter'),
            ('can_delete_newsletter', 'Can delete newsletter'),
        ]

    def is_active(self):
        return self.start_time <= timezone.now() <= self.end_time and self.status == 'Запущена'

    def duration(self):
        # Вычисление продолжительности рассылки в минутах
        if self.end_time > self.start_time:
            return (self.end_time - self.start_time).total_seconds() / 60  # в минутах
        return 0  # Если end_time <= start_time, возвращаем 0 минут

    def __str__(self):
        return f'Рассылка: {self.message.subject} ({self.status})'


class Attempt(models.Model):
    newsletter = models.ForeignKey('Newsletter', on_delete=models.CASCADE, related_name='attempts')
    recipient = models.ForeignKey('Recipient', on_delete=models.CASCADE, null=True)  # Разрешить null
    attempt_time = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=[('Успешно', 'Успешно'), ('Не успешно', 'Не успешно')])
    server_response = models.TextField()

    def __str__(self):
        return f'Попытка для {self.recipient.email} ({self.status})'
