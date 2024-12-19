from django.urls import path

from . import views

app_name = 'mailing'

urlpatterns = [
    path('', views.StatisticsView.as_view(), name='statistics'),
    path('dashboard/', views.ManagerDashboardView.as_view(), name='dashboard'),
    path('mailing/', views.MailingView.as_view(), name='mailing'),
    path('add_recipient/', views.AddRecipientView.as_view(), name='add_recipient'),
    path('edit_recipient/<pk>/', views.EditRecipientView.as_view(), name='edit_recipient'),
    path('add_message/', views.AddMessageView.as_view(), name='add_message'),
    path('edit_message/<pk>/', views.EditMessageView.as_view(), name='edit_message'),
    path('delete/<str:object_type>/<int:pk>/', views.DeleteObjectView.as_view(), name='delete_object'),
    path('newsletter/', views.CreateNewsletterView.as_view(), name='create_newsletter'),
    path('newsletters/<int:pk>/attempts/', views.AttemptListView.as_view(), name='newsletter_attempts'),
    path('my_newsletters/', views.MyNewslettersView.as_view(), name='my_newsletters'),
    path('send_newsletter/<pk>/', views.SendNewsletterView.as_view(), name='send_newsletter'),
    path('edit_newsletter/<pk>/', views.EditNewsletterView.as_view(), name='edit_newsletter'),
    path('delete_newsletter/<pk>/', views.DeleteNewsletterView.as_view(), name='delete_newsletter'),
    path('newsletter/<int:pk>/pause/', views.PauseNewsletterView.as_view(), name='pause_newsletter'),
]
