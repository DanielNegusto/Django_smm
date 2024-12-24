from django.urls import path
from django.contrib.auth import views as auth_views

from users.views import (
    RegisterView,
    ProfileUpdateView,
    activate,
    CustomLoginView,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
)

app_name = "users"

urlpatterns = [
    path(
        "login/",
        CustomLoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="mailing:statistics"),
        name="logout",
    ),
]
