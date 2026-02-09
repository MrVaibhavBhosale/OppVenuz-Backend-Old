"""
This file is used for creating models under users app.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from model_utils import Choices
from .managers import CustomUserManager
from rest_framework_simplejwt.tokens import RefreshToken


class State(models.Model):
    state_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.state_name}"


class City(models.Model):
    """
    Class for creating models for cities available on platform.
    """
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=False)
    city_name = models.CharField(max_length=100, null=False, blank=False)
    image = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.state} - {self.city_name}"


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Class for creating CustomUser by extending django's AbstractBaseUser class.
    """
    Role_Choice = Choices(
        ('SUPER_ADMIN', 'Super Admin'),
        ('USER', 'User'),
        ('VENDOR', 'Vendor'),
    )

    Status_Choice = Choices(
        ('ACTIVE', 'Active'),
        ('PENDING', 'Pending'),
        ('DELETED', 'Deleted'),
        ('SUSPENDED', 'Suspended')
    )

    Payment_Choice = Choices(
        ('PENDING', 'Pending'),
        ('DONE', 'Done')
    )

    fullname = models.CharField(max_length=100, null=True, blank=False)
    email = models.EmailField(_('email address'), unique=True, null=True,
                              error_messages={'unique': 'An account with this email address already exists.'})
    image = models.URLField(null=True, max_length=500)
    contact_number = models.TextField(max_length=40, null=True, blank=False)
    address_state = models.CharField(max_length=100, null=True, blank=False)
    address = models.TextField(max_length=200, null=True, blank=False)
    state = models.ForeignKey(State, null=True, blank=False, related_name='users', on_delete=models.SET_NULL)
    city = models.ForeignKey(City, null=True, blank=False, related_name='users', on_delete=models.SET_NULL)
    is_existing_user = models.BooleanField(default=False)
    otp = models.IntegerField(null=True, blank=False)
    otp_created_at = models.DateTimeField(null=True, blank=False)
    status = models.CharField(max_length=10, choices=Status_Choice)
    role = models.CharField(max_length=20, null=False, blank=False, choices=Role_Choice)
    cart_url = models.URLField(null=True, blank=False)
    payment_status = models.CharField(max_length=20, null=False, blank=False, choices=Payment_Choice, default="PENDING")
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_cart_url_updated = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['fullname', 'contact_number']

    objects = CustomUserManager()

    def __str__(self):
        """
        Function to return email.
        """
        return f"{self.email} - {self.role} - {self.status}"
    
    def set_address(self):
        self.address = self.city.city_name if self.city else None
        self.save()
    
    def set_address_state(self):
        self.address_state = self.state.state_name if self.state else None
        self.save()

    @property
    def get_address(self) -> str:
        return self.city.city_name if self.city else None
    
    @property
    def get_address_state(self) -> str:
        return self.state.state_name if self.state else None

    def set_is_existing_user(self, flag=True):
        self.is_existing_user = flag
        self.save()

    def reset_otp(self):
        self.otp = None
        self.otp_created_at = None
        self.save()

    def add_service_to_favorites(self, service):
        # Toggle the favorite status
        if service in self.favorites.all():
            # Service is already a favorite, remove it
            self.favorites.remove(service)
            return 0
        else:
            # Service is not a favorite, add it
            self.favorites.add(service)
            return 1

    def is_favorite(self, service_id):
        return self.favorites.filter(id=service_id).exists()
    
    def like_dislike_article(self, article_id):
        if self.articlelike_set.filter(user_id=self, article_id_id=article_id).exists():
            self.articlelike_set.filter(user_id=self, article_id_id=article_id).delete()
            return 0
        else:
            self.articlelike_set.create(user_id=self, article_id_id=article_id)
            return 1
        
class AdminRolesMaster(models.Model):
    """
    Class for creating models for roles available on platform with specific IDs.
    """
    id = models.IntegerField(primary_key=True)
    role_name = models.CharField(max_length=100, null=False, blank=False)
    role_desc = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.role_name}"

class AdminRoles(models.Model):
    """
    Class for creating models for roles assigned to users.
    """
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False, blank=False)
    role_id = models.ForeignKey(AdminRolesMaster, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return f"{self.user} - {self.role}"


class BlackListedToken(models.Model):
    """
    Class for creating blacklisted tokens which have already been used.
    """
    token = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Class container containing information of the model.
        """
        unique_together = ("token",)


class ForgotPasswordRequest(models.Model):
    """
    Class for creating models for forgot password requested by users.
    """
    Request_Status_Choice = Choices(
        ('U', 'Used'),
        ('UU', 'Unused'),
        ('E', 'Expired'),
    )
    email = models.EmailField(max_length=100)
    otp = models.CharField(max_length=5, null=False)
    request_status = models.CharField(max_length=2, choices=Request_Status_Choice)
    created_at = models.DateTimeField(null=False)

    def __str__(self):
        """
        Function to return email.
        """
        return self.email


class InviteUser(models.Model):
    """
    Class for creating models for inviting users on platform.
    """
    Role_Choice = Choices(
        ('SUPER_ADMIN', 'Super Admin'),
        ('USER', 'User'),
        ('VENDOR', 'Vendor'),
    )

    Status = Choices(
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted')
    )

    email = models.EmailField(max_length=100)
    fullname = models.CharField(max_length=100, null=False, blank=False)
    invited_by = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, null=True, choices=Role_Choice)
    invite_status = models.CharField(max_length=20, null=True, choices=Status)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """
        Function to return email.
        """
        return self.email


class Notification(models.Model):
    """
    Class for creating models for notification.
    """
    Read_Status = Choices(
        ('UR', 'UnRead'),
        ('R', 'Read')
    )

    Action = Choices(
        ('CELEBRITY_ENQUIRY', 'CELEBRITY_ENQUIRY'),
        ('SERVICE_APPROVAL', 'SERVICE_APPROVAL'),
        ('SERVICE_REJECTED', 'SERVICE_REJECTED'),
        ('SERVICE_ENQUIRY', 'SERVICE_ENQUIRY'),
        ('SERVICE_SUSPENDED', 'SERVICE_SUSPENDED'),
        ('CART_SHARE', 'CART_SHARE'),
        ('ARTICLE_PUBLISHED', 'ARTICLE_PUBLISHED'),
        ('CELEBRITY_ADDED', 'CELEBRITY_ADDED'),
        ('VENDOR_ADDED', 'VENDOR_ADDED'),
        ('NEW_PROMOTION', 'NEW_PROMOTION'),
        ('SERVICE_LIKED', 'SERVICE_LIKED'),
        ('SERVICE_FAV', 'SERVICE_FAV'),
    )
    message = models.TextField(max_length=1000, null=False, blank=False)
    user_id = models.ForeignKey(CustomUser, null=True, blank=False, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, null=True, choices=Read_Status)
    notification_type = models.CharField(max_length=30, null=True, choices=Action)
    params = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class ContactUs(models.Model):
    """
    Class for creating models for user queries.
    """
    user_id = models.ForeignKey(CustomUser, null=False, blank=False, on_delete=models.CASCADE)
    email = models.EmailField(max_length=100, null=False, blank=False)
    message = models.TextField(max_length=1000, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)


class EmailVerification(models.Model):
    """
    Class for creating model for verifying email address of user.
    """
    email = models.EmailField(max_length=100, null=False, blank=False)
    secret_code = models.IntegerField(null=False, blank=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)


class PhoneVerification(models.Model):
    """
    Class for creating model for verifying email address of user.
    """
    phone_number = models.TextField(null=False, blank=False)
    secret_code = models.IntegerField(null=False, blank=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)


def get_tokens_for_user(user_name):
    """
    function to creates and returns JWT token in response
    """
    refresh = RefreshToken.for_user(user_name)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class PromotionalMesssage(models.Model):
    """
    Class for creating and sending Promotional message to user by userType.
    """
    Role_Choice = Choices(
        ('SUPER_ADMIN', 'Super Admin'),
        ('USER', 'User'),
        ('VENDOR', 'Vendor'),
    )
    title = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    img_url = models.URLField(blank=True, null=True)
    userType =  models.CharField(max_length=20, null=False, blank=False, choices=Role_Choice)
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    updated_at = models.DateTimeField(auto_now=timezone.now)

    def __str__(self):
        """
        Function to return title.
        """
        return self.title

