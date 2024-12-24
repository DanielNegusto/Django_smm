from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from users.models import CustomUser


class Command(BaseCommand):
    help = "Add a user by email to the Managers group"

    def add_arguments(self, parser):
        parser.add_argument(
            "email", type=str, help="Email of the user to add to the Managers group"
        )

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        group, created = Group.objects.get_or_create(name="Менеджеры")

        try:
            user = CustomUser.objects.get(email=email)
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f"User  {user.username} added to Managers group")
            )
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User  with email {email} does not exist")
            )
