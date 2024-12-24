import logging
import threading
import time

from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    ListView,
    View,
    TemplateView,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from users.models import CustomUser
from .mixins import UserMessagesAndRecipientsMixin, ManagerRequiredMixin
from .models import Attempt, Recipient, Message, Newsletter
from .forms import NewsletterForm, MessageForm, RecipientForm

logger = logging.getLogger(__name__)


class MailingView(LoginRequiredMixin, ListView):
    model = Newsletter
    template_name = "mailing/mailing.html"
    context_object_name = "newsletters"

    @method_decorator(cache_page(10))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages_users"] = Message.objects.filter(owner=self.request.user)
        context["recipients"] = Recipient.objects.filter(owner=self.request.user)
        return context


class AddMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/add_message.html"
    success_url = reverse_lazy("mailing:mailing")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        print(f"Message created: {form.instance}")

        # Обновление кэша
        cache_key = f'user_{self.request.user.id}_messages'
        cache.delete(cache_key)  # Удаление старого кэша

        return response


class EditMessageView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/add_message.html"
    success_url = reverse_lazy("mailing:mailing")


class DeleteObjectView(LoginRequiredMixin, UserMessagesAndRecipientsMixin, View):
    @staticmethod
    def get(request, pk, object_type):
        if object_type == "message":
            obj = get_object_or_404(Message, pk=pk)
        elif object_type == "recipient":
            obj = get_object_or_404(Recipient, pk=pk)
        else:
            return redirect("mailing:mailing")

        return render(
            request,
            "mailing/delete_message.html",
            {"object": obj, "object_type": object_type},
        )

    @staticmethod
    def post(request, pk, object_type):
        if object_type == "message":
            obj = get_object_or_404(Message, pk=pk)
            cache_key = 'message_{}'.format(obj.id)  # Уникальный ключ для сообщения
        elif object_type == "recipient":
            obj = get_object_or_404(Recipient, pk=pk)
            cache_key = 'recipient_{}'.format(obj.id)  # Уникальный ключ для получателя
        else:
            return redirect("mailing:mailing")

        obj.delete()
        cache.delete(cache_key)
        return redirect("mailing:mailing")


class AddRecipientView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/add_recipient.html"
    success_url = reverse_lazy("mailing:mailing")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        print(f"Recipient created: {form.instance}")
        return response


class EditRecipientView(LoginRequiredMixin, UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/add_recipient.html"
    success_url = reverse_lazy("mailing:mailing")


# CRUD for Newsletters
class CreateNewsletterView(LoginRequiredMixin, CreateView):
    model = Newsletter
    form_class = NewsletterForm
    template_name = "mailing/create_newsletter.html"
    success_url = reverse_lazy("mailing:my_newsletters")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class EditNewsletterView(LoginRequiredMixin, UpdateView):
    model = Newsletter
    form_class = NewsletterForm
    template_name = "mailing/create_newsletter.html"
    success_url = reverse_lazy("mailing:my_newsletters")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        newsletter = form.save(commit=False)
        newsletter.status = "Создана"
        newsletter.save()
        messages.success(self.request, "Рассылка успешно обновлена.")
        return super().form_valid(form)


class DeleteNewsletterView(LoginRequiredMixin, DeleteView):
    model = Newsletter
    template_name = "mailing/delete_newsletter.html"
    success_url = reverse_lazy("mailing:my_newsletters")


class MyNewslettersView(LoginRequiredMixin, ListView):
    model = Newsletter
    template_name = "mailing/my_newsletters.html"
    context_object_name = "newsletters"

    @method_decorator(cache_page(10))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        return Newsletter.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_time = timezone.now()

        for newsletter in context["newsletters"]:
            if newsletter.start_time and newsletter.end_time:
                if current_time < newsletter.start_time:
                    remaining_time = newsletter.start_time - current_time
                else:
                    remaining_time = newsletter.end_time - current_time

                if remaining_time.total_seconds() <= 0:
                    newsletter.remaining_hours = 0
                    newsletter.remaining_minutes = 0
                    newsletter.remaining_seconds = 0
                else:
                    newsletter.remaining_hours = (
                        remaining_time.days * 24 + remaining_time.seconds // 3600
                    )
                    newsletter.remaining_minutes = (remaining_time.seconds // 60) % 60
                    newsletter.remaining_seconds = remaining_time.seconds % 60

        return context


def send_newsletter(newsletter_id):
    try:
        newsletter = Newsletter.objects.get(id=newsletter_id)
    except Newsletter.DoesNotExist:
        return

    recipients = newsletter.recipients.all()
    if not recipients.exists():
        return

    interval = 120

    end_time = newsletter.end_time

    if end_time.tzinfo is None:
        end_time = timezone.make_aware(end_time)

    current_time = timezone.now()

    if current_time > end_time:
        newsletter.status = "Завершена"
        newsletter.save()
        return

    while timezone.now() < end_time:
        newsletter.refresh_from_db()
        if newsletter.status == "Приостановлена":
            return

        for recipient in recipients:
            try:
                validate_email(recipient.email)

                send_mail(
                    newsletter.message.subject,
                    newsletter.message.body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=False,
                )
                Attempt.objects.create(
                    newsletter=newsletter,
                    recipient=recipient,
                    status="Успешно",
                    server_response="Сообщение отправлено",
                )

            except ValidationError:
                Attempt.objects.create(
                    newsletter=newsletter,
                    recipient=recipient,
                    status="Не успешно",
                    server_response="Некорректный адрес электронной почты",
                )

            except Exception as e:
                Attempt.objects.create(
                    newsletter=newsletter,
                    recipient=recipient,
                    status="Не успешно",
                    server_response=str(e),
                )

        time.sleep(interval)

    newsletter.status = "Завершена"
    newsletter.save()


class SendNewsletterView(LoginRequiredMixin, View):
    @staticmethod
    def post(request, pk):
        newsletter = get_object_or_404(Newsletter, pk=pk)

        if newsletter.status not in ["Создана", "Запущена", "Приостановлена"]:
            messages.error(request, "Эту рассылку нельзя отправить.")
            return redirect("mailing:my_newsletters")

        newsletter.status = "Запущена"
        newsletter.save()

        threading.Thread(target=send_newsletter, args=(newsletter.id,)).start()

        messages.success(request, "Рассылка запущена.")
        return redirect("mailing:my_newsletters")


class PauseNewsletterView(LoginRequiredMixin, View):
    @staticmethod
    def post(request, pk):
        newsletter = get_object_or_404(Newsletter, pk=pk)
        newsletter.status = "Приостановлена"
        newsletter.save()
        messages.success(request, "Рассылка приостановлена.")
        return redirect("mailing:my_newsletters")


class AttemptListView(ListView):
    model = Attempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        newsletter_id = self.kwargs.get("pk")
        return Attempt.objects.filter(newsletter_id=newsletter_id).order_by(
            "-attempt_time"
        )


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = "mailing/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        user_newsletters = Newsletter.objects.filter(owner=user)

        context["total_newsletters"] = user_newsletters.count()
        context["active_newsletters"] = user_newsletters.filter(
            status="Запущена"
        ).count()
        context["unique_recipients"] = (
            Recipient.objects.filter(newsletter__in=user_newsletters).distinct().count()
        )

        context["total_attempts"] = Attempt.objects.filter(
            newsletter__owner=user
        ).count()
        context["successful_attempts"] = Attempt.objects.filter(
            newsletter__owner=user, status="Успешно"
        ).count()
        context["unsuccessful_attempts"] = Attempt.objects.filter(
            newsletter__owner=user, status="Не успешно"
        ).count()

        context["is_manager"] = user.groups.filter(name="Менеджеры").exists()

        return context


class ManagerDashboardView(ManagerRequiredMixin, ListView):
    model = CustomUser
    template_name = "mailing/manager_dashboard.html"
    context_object_name = "users"

    def get_queryset(self):
        return CustomUser.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["newsletters"] = Newsletter.objects.all()
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        if "block_user" in request.POST:
            user_id = request.POST.get("user_id")
            user = get_object_or_404(CustomUser, id=user_id)
            user.is_active = False
            user.save()

        elif "unblock_user" in request.POST:
            user_id = request.POST.get("user_id")
            user = get_object_or_404(CustomUser, id=user_id)
            user.is_active = True
            user.save()

        elif "stop_newsletter" in request.POST:
            newsletter_id = request.POST.get("newsletter_id")
            newsletter = get_object_or_404(Newsletter, id=newsletter_id)
            newsletter.status = "Отключена"
            newsletter.save()

        return redirect("mailing:dashboard")
