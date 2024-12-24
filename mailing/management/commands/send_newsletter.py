from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from mailing.models import Newsletter, Attempt
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Отправить рассылку по её ID"

    def add_arguments(self, parser):
        parser.add_argument("newsletter_id", type=int, help="ID рассылки")

    def handle(self, *args, **kwargs):
        newsletter_id = kwargs["newsletter_id"]
        try:
            newsletter = Newsletter.objects.get(id=newsletter_id)
        except Newsletter.DoesNotExist:
            self.stdout.write(self.style.ERROR("Рассылка не найдена."))
            return

        if newsletter.status not in ["Создана", "Запущена"]:
            self.stdout.write(self.style.WARNING("Эту рассылку нельзя отправить."))
            return

        # Обновляем статус на "Запущена"
        newsletter.status = "Запущена"
        newsletter.save()

        recipients = newsletter.recipients.all()
        attempts = []

        for recipient in recipients:
            try:
                send_mail(
                    subject=newsletter.message.subject,
                    message=newsletter.message.body,
                    from_email="from@example.com",  # Укажите ваш email
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                attempts.append(
                    Attempt(
                        newsletter=newsletter,
                        recipient=recipient,
                        status="Успешно",
                        server_response="Message sent successfully.",
                    )
                )
            except Exception as e:
                error_message = str(e)
                logger.error(
                    f"Ошибка отправки письма для {recipient.email}: {error_message}"
                )
                attempts.append(
                    Attempt(
                        newsletter=newsletter,
                        recipient=recipient,
                        status="Не успешно",
                        server_response=error_message,
                    )
                )

        # Сохраняем попытки
        Attempt.objects.bulk_create(attempts)

        newsletter.status = "Завершена"
        newsletter.save()

        self.stdout.write(self.style.SUCCESS("Рассылка завершена."))
