from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import View
from .models import Message, Recipient


class UserMessagesAndRecipientsMixin(View):
    def get_context_data(self, **kwargs):
        # Если ваш миксин используется в классе, который наследует от View,
        # добавьте проверку на наличие метода get_context_data
        context = (
            kwargs  # Используйте kwargs, если метод не определён в родительском классе
        )
        context["messages_users"] = Message.objects.filter(owner=self.request.user)
        context["recipients"] = Recipient.objects.filter(owner=self.request.user)
        return context


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        request = self.request
        return request.user.groups.filter(name="Менеджеры").exists()
