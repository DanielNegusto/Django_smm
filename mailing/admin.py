from django.contrib import admin
from .models import Recipient, Message, Newsletter, Attempt

admin.site.register(Recipient)
admin.site.register(Message)
admin.site.register(Newsletter)
admin.site.register(Attempt)
