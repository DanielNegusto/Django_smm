from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, FormView
from django.core.mail import send_mail
from django.contrib.auth.views import (
    LoginView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib.messages import success
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages

from .forms import UserRegistrationForm, ProfileUpdateForm


class RegisterView(FormView):
    template_name = "users/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("mailing:home")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        domain = get_current_site(self.request).domain
        activation_link = f"http://{domain}/users/activate/{uid}/{token}/"
        subject = "Подтвердите свою регистрацию"
        message = (
            f"Здравствуйте, {user.username}! Пожалуйста, "
            f"подтвердите свою регистрацию, перейдя по следующей ссылке: {activation_link}"
        )
        send_mail(subject, message, "admin@example.com", [user.email])

        return redirect("mailing:statistics")


class CustomLoginView(LoginView):
    template_name = "users/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            messages.error(
                self.request,
                "Пожалуйста, проверьте свою почту и подтвердите регистрацию.",
            )
            return self.form_invalid(
                form
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        email = form.cleaned_data.get(
            "username"
        )
        if email:
            try:
                user = self.get_user(email)
                if user and not user.is_active:
                    messages.error(
                        self.request,
                        "Пожалуйста, проверьте свою почту и подтвердите регистрацию.",
                    )
            except User.DoesNotExist:
                pass
        return super().form_invalid(form)

    @staticmethod
    def get_user(email):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.get(email=email)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUpdateForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("mailing:home")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        # Отправляем сообщение об успешном обновлении профиля
        success(self.request, "Ваш профиль был успешно обновлен!")
        return super().form_valid(form)


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request, "Ваш аккаунт был активирован! Теперь вы можете войти."
        )
        return redirect(
            "mailing:mailing"
        )  # Перенаправьте на страницу входа или другую нужную страницу
    else:
        messages.error(request, "Ссылка для активации недействительна!")
        return render(request, "users/activation_invalid.html")


class CustomPasswordResetView(PasswordResetView):
    email_template_name = "users/password_reset_email.html"
    template_name = "users/password_reset.html"
    success_url = reverse_lazy("users:password_reset_done")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["protocol"] = self.request.scheme
        context["domain"] = self.request.get_host()
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"
