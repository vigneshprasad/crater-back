from django.contrib.auth.models import UserManager as Manager


class UserManager(Manager):

    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        return super().create_superuser(username='Admin', email=email, password=password)
