from django.contrib.auth import authenticate
from pandas.core.computation.ops import isnumeric
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from service.models import VendorService
from users.utils import set_user_city_state

from utilities import messages
from .models import (
    City,
    CustomUser,
    InviteUser,
    AdminRoles,
    Notification,
    BlackListedToken,
    EmailVerification,
    PhoneVerification,
    ForgotPasswordRequest,
    State,
    PromotionalMesssage,
)
from oauth2_provider.models import Application
from fcm_django.models import FCMDevice


class VerifyUserSerializer(serializers.Serializer):
    """
    User OTP verification serializer
    """

    email_or_phone = serializers.CharField()
    otp = serializers.IntegerField(required=False)
    expire_otp = serializers.BooleanField(default=False)

    class Meta:
        fields = ["email_or_phone", "otp", "expire_otp"]


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    Class for defining how user registration request and response object should look like.
    """

    class Meta:
        """
        Class container containing information of the model.
        """

        model = CustomUser
        fields = [
            "fullname",
            "email",
            "password",
            "role",
            "image",
            "contact_number",
            "status",
            "address_state",
            "address",
        ]
        extra_kwargs = {
            "fullname": {
                "error_messages": {
                    "blank": "Fullname is required.",
                    "null": "Fullname is required.",
                    "required": "Fullname is required.",
                }
            },
            "username": {
                "error_messages": {
                    "blank": "Username is required.",
                    "null": "Username is required.",
                    "required": "Username is required.",
                }
            },
            "email": {
                "error_messages": {
                    "blank": "Email is required.",
                    "null": "Email is required.",
                    "required": "Email is required.",
                }
            },
            "password": {"write_only": True},
        }

    def validate(self, data):
        """
        Function for validating and returning the created instance
         based on the validated data of the user.
        """
        password = data["password"]
        fullname = data["fullname"]
        password_length = len(password)

        if not 5 <= password_length <= 16:
            raise serializers.ValidationError(messages.PASS_LIMIT)

        if not all(char.isalpha() or char.isspace() for char in fullname):
            raise serializers.ValidationError("Fullname should only contain alphabets.")

        return data

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
         based on the validated data of the user.
        """
        user = CustomUser.objects.create_user(
            fullname=validated_data.pop("fullname"),
            email=validated_data.pop("email"),
            password=validated_data.pop("password"),
            contact_number=validated_data.pop("contact_number"),
            image=validated_data.pop("image"),
            status=validated_data.pop("status"),
            role=validated_data.pop("role"),
            address_state=validated_data.get("address_state", None),
            address=validated_data.pop("address"),
        )
        return user


class SuperUserSignUpSerializer(UserSignUpSerializer):
    """
    Serializer for creating a admin user.
    """

    class Meta(UserSignUpSerializer.Meta):
        fields = ["fullname", "email", "password", "contact_number"]
        extra_kwargs = {
            "fullname": {
                "error_messages": {
                    "blank": "Fullname is required.",
                    "null": "Fullname is required.",
                    "required": "Fullname is required.",
                }
            },
            "email": {
                "error_messages": {
                    "blank": "Email is required.",
                    "null": "Email is required.",
                    "required": "Email is required.",
                }
            },
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Function for creating and returning the created admin user instance.
        """
        user = CustomUser.objects.create_admin_users(
            fullname=validated_data.pop("fullname"),
            email=validated_data.pop("email"),
            password=validated_data.pop("password"),
            contact_number=validated_data.pop("contact_number"),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Class for authorizing user for correct login credentials.
    """

    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    default_error_messages = {
        "inactive_account": _("User account is disabled."),
        "invalid_credentials": _(
            "Either email or password you have entered is incorrect."
        ),
        "invalid_password": _(messages.PASS_NUMBER_ONLY),
    }

    def __init__(self, *args, **kwargs):
        """
        Constructor Function for initializing UserLoginSerializer.
        """
        super(UserLoginSerializer, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        """
        Function for validating and returning the created instance
         based on the validated data of the user.
        """
        password = attrs.pop("password")       
        email = attrs.pop("email").strip()
        self.user = authenticate(username=email, password=password)
        if self.user:
            if not self.user.is_active:
                raise serializers.ValidationError(
                    self.error_messages["inactive_account"]
                )
            return attrs
        else:
            raise serializers.ValidationError(
                self.error_messages["invalid_credentials"]
            )


class ListAdminUsersSerializer(serializers.ModelSerializer):
    """
    Class for listing all the admin users.i. e. role = 'SUPER_ADMIN'
    """

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "fullname",
            "email",
            "contact_number",
            "status",
            "role",
            "address_state",
            "address",
        ]


class GetAdminUserRolesSerializer(serializers.ModelSerializer):
    """
    Class for listing all roles of admin users joining AdminRoles And AdminRolesMaster
    """

    class Meta:
        model = AdminRoles
        fields = ["role_id"]


class SaveAdminUserRolesSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class ForgotPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForgotPasswordRequest
        fields = (
            "email",
            "otp",
            "request_status",
            "created_at",
        )

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
         based on the validated data of the ForgetPassword Model.
        """
        forgot_password_data, created = ForgotPasswordRequest.objects.update_or_create(
            email=validated_data.get("email"),
            defaults={
                "request_status": validated_data.pop("request_status"),
                "otp": validated_data.pop("otp", None),
                "created_at": validated_data.pop("created_at"),
            },
        )
        return forgot_password_data


class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerification
        fields = ("email", "secret_code", "is_verified")

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
         based on the validated data of the EmailVerification Model.
        """
        verification_data, created = EmailVerification.objects.update_or_create(
            email=validated_data.get("email"),
            defaults={
                "is_verified": validated_data.pop("is_verified"),
                "secret_code": validated_data.pop("secret_code", None),
            },
        )
        return verification_data


class PhoneVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneVerification
        fields = ("phone_number", "secret_code", "is_verified")

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
        based on the validated data of the PhoneVerification Model.
        """
        verification_data, created = PhoneVerification.objects.update_or_create(
            phone_number=validated_data.get("phone_number"),
            defaults={
                "is_verified": validated_data.pop("is_verified"),
                "secret_code": validated_data.pop("secret_code", None),
            },
        )
        return verification_data


class InviteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteUser
        fields = ["id", "fullname", "email", "invited_by", "role", "invite_status"]

    def create(self, validated_data):
        invite_user, created = InviteUser.objects.update_or_create(
            email=validated_data.get("email"),
            defaults={
                "fullname": validated_data.get("fullname"),
                "invited_by": validated_data.get("invited_by"),
                "role": validated_data.get("role"),
                "invite_status": validated_data.get("invite_status"),
            },
        )

        return invite_user


class UpdateUserPasswordSerializer(serializers.ModelSerializer):
    """
    Class for defining how user forgot password request and response object should look like.
    """

    class Meta:
        """
        Class container containing information of the model.
        """

        model = CustomUser
        fields = ["email", "password"]

        default_error_messages = {
            "invalid_password": _(messages.PASS_NUMBER_ONLY),
            "password_limit": _(messages.PASS_LIMIT),
        }

    def update(self, instance, validated_data):
        """
        Function for updating and returning the updated instance
         based on the validated data of the user.
        """
        password = validated_data.pop("password")

        if not 5 <= len(password) <= 16:
            raise serializers.ValidationError(self.error_messages["password_limit"])

        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Class for defining how change password request object should be.
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "fullname",
            "is_existing_user",
            "contact_number",
            "image",
            "status",
            "address_state",
            "address",
            "reason",
        ]

    def update(self, instance, validated_data):
        """
        Function for updating and returning the updated instance
         based on the validated data of the user.
        """
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = "__all__"


class UpdateUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "status"]


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "state_name"]


class CitySerializer(serializers.ModelSerializer):
    """
    Class for defining how get city request object should be.
    """

    class Meta:
        model = City
        fields = ["id", "city_name"]


class FCMSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = [
            "id",
            "name",
            "active",
            "device_id",
            "registration_id",
            "type",
            "user_id",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user_id",
            "message",
            "status",
            "created_at",
            "notification_type",
            "params",
        ]


class BlackListSerializer(serializers.ModelSerializer):
    """
    Class for defining how blacklisted token request and response object should look like.
    """

    class Meta:
        """
        Class container containing information of the model.
        """

        model = BlackListedToken
        fields = ("token",)


class AddVendorSerializer(serializers.ModelSerializer):
    service_id = serializers.ListField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "fullname",
            "email",
            "role",
            "contact_number",
            "status",
            "address_state",
            "address",
            "service_id",
        ]
        extra_kwargs = {
            "fullname": {
                "required": True,
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Fullname"),
                    "null": messages.REQUIRED_FIELD.format("Fullname"),
                    "required": messages.REQUIRED_FIELD.format("Fullname"),
                },
            },
            "email": {
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Email"),
                    "null": messages.REQUIRED_FIELD.format("Email"),
                    "required": messages.REQUIRED_FIELD.format("Email"),
                }
            },
            "contact_number": {
                "required": True,
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Contact number"),
                    "null": messages.REQUIRED_FIELD.format("Contact number"),
                    "required": messages.REQUIRED_FIELD.format("Contact number"),
                },
            },
            "address_state": {
                "required": True,
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Address state"),
                    "null": messages.REQUIRED_FIELD.format("Address state"),
                    "required": messages.REQUIRED_FIELD.format("Address state"),
                },
            },
            "address": {
                "required": True,
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Address"),
                    "null": messages.REQUIRED_FIELD.format("Address"),
                    "required": messages.REQUIRED_FIELD.format("Address"),
                },
            },
            "service_id": {
                "required": True,
                "error_messages": {
                    "blank": messages.REQUIRED_FIELD.format("Service"),
                    "null": messages.REQUIRED_FIELD.format("Service"),
                    "required": messages.REQUIRED_FIELD.format("Service"),
                },
            },
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Function for creating and returning the created instance
         based on the validated data of the user.
        """
        address_state = validated_data.get("address_state", None)
        address = validated_data.get("address", None)
        user = CustomUser.objects.create_user(
            fullname=validated_data.pop("fullname"),
            email=validated_data.pop("email"),
            contact_number=validated_data.pop("contact_number"),
            status=validated_data.pop("status"),
            role=validated_data.pop("role"),
            address_state=validated_data.get("address_state", None),
            address=validated_data.pop("address"),
        )
        city = (
            City.objects.filter(city_name=address, state__state_name=address_state)
            .order_by("-is_listed")
            .first()
        )
        user.state_id = city.state_id
        user.city = city
        user.save()
        return user


class CreateProfileSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    fullname = serializers.CharField(max_length=100)
    state = serializers.IntegerField()
    city = serializers.IntegerField(required=False)


class UserDetailSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()
    address_state = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "fullname",
            "is_existing_user",
            "role",
            "status",
            "contact_number",
            "image",
            "address",
            "address_state",
            "state",
            "city",
            "cart_url",
            "reason",
        ]
        extra_kwargs = {
            "state": {
                "write_only": True,
            },
            "city": {
                "write_only": True,
            },
        }

    def get_address(self, instance):
        set_user_city_state(instance)
        return instance.city.city_name if instance.city else None

    def get_address_state(self, instance):
        return instance.state.state_name if instance.state else None

    def get_role(self, instance):
        return instance.role

    def get_status(self, instance):
        return instance.status


class CityDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = City
        fields = ["id", "state", "city_name", "is_listed", "is_featured"]

    def validate(self, attrs):
        state = attrs.get("state")
        city_name = attrs.get("city_name")
        attrs.setdefault("is_listed", True)
        attrs.setdefault("is_featured", True)
        cities = City.objects.filter(state=state, city_name=city_name.title())
        if cities.exists():
            raise serializers.ValidationError(
                {"message": messages.CITY_EXISTS.format(city_name.title(), state)}
            )
        return attrs


class CityListSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source="state.state_name", read_only=True)

    class Meta:
        model = City
        fields = ["id", "state", "city_name", "image", "is_featured", "is_listed"]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["venue_count"] = VendorService.objects.filter(
            approval_status="A",
            city=instance.city_name or None,
            service_id__slug="venue",
        ).count()
        return response


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "fullname",
            "contact_number",
            "image",
            "status",
            "address_state",
            "address",
            "state",
            "city",
            "role",
            "cart_url",
            "reason",
        ]


class PromotionalMesssageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionalMesssage
        fields = ["id", "title", "description", "img_url", "userType"]
