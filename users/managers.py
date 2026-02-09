"""
This file is used for creating custom user manager for the correspondent custom user.
"""
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Class for creating custom manager for managing custom user.
    """
    def create_user(self, email=None, fullname=None, password=None, contact_number=None, image=None, role="USER",
                    status="ACTIVE", address_state=None, address=None, **extra_fields):
        """
        Function for creating user w.r.t custom user.
        """
        user = self.model(
            email=self.normalize_email(email)
        )
        user.fullname = fullname
        user.image = image
        user.status = status
        user.role = role
        user.contact_number = contact_number
        user.address_state = address_state
        user.address = address
        user.is_superuser = False
        user.is_active = True
        user.is_staff = False
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, fullname, email, password, contact_number=None):
        """
        Function for creating super user.
        """
        user = self.create_user(
            email,
            fullname,
            password,
            contact_number,
            image=None,
            role='SUPER_ADMIN',
            status='ACTIVE',
            address=None
        )
        user.is_superuser = True
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_admin_users(self, email, fullname, password, contact_number=None):
        """
        Function for creating admin user.
        """
        user = self.create_user(
            email,
            fullname,
            password,
            contact_number,
            image=None,
            role='SUPER_ADMIN',
            status='ACTIVE',
            address=None
        )
        user.is_superuser = False
        user.is_active = True
        user.is_admin = False
        user.is_staff = True
        user.save(using=self._db)
        return user
