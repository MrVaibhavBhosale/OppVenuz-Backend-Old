import os
import jwt
import json
import random
import requests
import sendgrid
import boto3
import branchio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter
from django.db.models import Q
from oppvenuz.settings.settings import (
    BASE_DIR,
    PROJECT_ROOT,
    STAGING_API_URL,
    PROD_API_URL,
    SOCIAL_AUTH_APPLE_ID_TEAM,
)
from fcm_django.models import FCMDevice
from sendgrid.helpers.mail import Mail, Email, Personalization
from rest_framework.views import APIView
from python_http_client import exceptions
from datetime import datetime, timedelta
from decouple import config
from django.db.models import Count
from rest_framework import status
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_social_oauth2.authentication import SocialAuthentication
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from utilities import constants

from utilities import messages
from utilities.commonutils import send_email, user_delete, deleted_vendor_service_remove
from utilities.constants import (
    FORGOT_PASSWORD_URL,
    USER_FORGOT_PASSWORD_URL,
    VENDOR_FORGOT_PASSWORD_URL,
    DELETED,
    VENDOR,
    ADMIN_VENDOR_REGISTRATION_TEMPLATE,
    ADMIN_REC_WHEN_VENDOR_REG_BY_ADMIN,
)
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    DestroyAPIView,
    GenericAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from users.permissions import IsSuperAdmin, IsTokenValid, IsSuperAdmin
from users.utils import (
    get_otp,
    send_sms,
    ResponseInfo,
    CustomPagination,
    generate_password,
    is_existing_user,
)
from .models import (
    City,
    PromotionalMesssage,
    CustomUser,
    AdminRoles,
    AdminRolesMaster,
    Notification,
    EmailVerification,
    PhoneVerification,
    ForgotPasswordRequest,
    get_tokens_for_user,
    State,
)
from service.models import VendorService
from feedbacks.models import TrackUserSession
from .serializers import (
    CityDetailSerializer,
    CityListSerializer,
    CreateProfileSerializer,
    FCMSerializer,
    CitySerializer,
    UserLoginSerializer,
    ListAdminUsersSerializer,
    GetAdminUserRolesSerializer,
    SaveAdminUserRolesSerializer,
    SuperUserSignUpSerializer,
    BlackListSerializer,
    UserSignUpSerializer,
    InviteUserSerializer,
    UpdateUserSerializer,
    ApplicationSerializer,
    NotificationSerializer,
    ForgotPasswordSerializer,
    ChangePasswordSerializer,
    UpdateUserStatusSerializer,
    PhoneVerificationSerializer,
    EmailVerificationSerializer,
    UpdateUserPasswordSerializer,
    StateSerializer,
    AddVendorSerializer,
    VerifyUserSerializer,
    UserDetailSerializer,
    UserDetailSerializer,
    PromotionalMesssageSerializer,
)
from service.serializers import AddVendorServiceSerializers
from oppvenuz.settings.settings import DEFAULT_FROM_EMAIL
from oauth2_provider.models import Application
from utilities.constants import FCM_BASE_URL
from service.utils import get_or_create_users_cart_url, update_user_cart_url
from utilities.mixins import CSVDownloadMixin
from firebase_admin.messaging import (
    Message,
    AndroidConfig,
    AndroidNotification,
    Notification as NotificationSend,
)
from django.conf import settings
from utilities.scheduler import (
    scheduler,
    send_promotional_mail_to_users,
    start_scheduler,
)

# load_dotenv()

# sg = sendgrid.SendGridAPIClient(config("SENDGRID_API_KEY"))
# client = branchio.Client(config("DEVELOP_BRANCH_API_KEY"))

dev_client = branchio.Client(config("DEVELOP_BRANCH_API_KEY"))
staging_client = branchio.Client(config("STAGING_BRANCH_API_KEY"))

# FCM_ENDPOINT = 'v1/projects/' + config("PROJECT_ID") + '/messages:send'
# FCM_URL = FCM_BASE_URL + '/' + FCM_ENDPOINT
# SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
# # FCM_FILE_PATH = str(BASE_DIR) + "/oppvenuz/firebase/oppvenuz-274310-firebase-adminsdk-mzl12-84b160d3f7.json"
# FCM_FILE_PATH = str(BASE_DIR) + config("FCM_JSON_SDK")
# print("FCM PATH", FCM_FILE_PATH)


# def _get_access_token(path):
#     """
#     Retrieve a valid access token that can be used to authorize requests.
#     :return: Access token .
#     """
#     credentials = ServiceAccountCredentials.from_json_keyfile_name(
#         path, SCOPES)
#     # print("PATH", path)
#     # print("CRED", credentials)
#     access_token_info = credentials.get_access_token()
#     return access_token_info.access_token
#     # [END retrieve_access_token]


# def _send_fcm_message(fcm_message, path):
#     """
#     Send HTTP request to FCM with given message.
#     Args:
#         fcm_message: JSON object that will make up the body of the request.
#     """
#     # [START use_access_token]
#     headers = {
#         'Authorization': 'Bearer ' + _get_access_token(path),
#         'Content-Type': 'application/json; UTF-8',
#     }
#     # [END use_access_token]
#     resp = requests.post(FCM_URL, data=json.dumps(fcm_message), headers=headers)
#     if resp.status_code == 200:
#         print('Message sent to Firebase for delivery, response:')
#         # print(resp.text)
#     else:
#         print('Unable to send message to Firebase')
#         print(resp.text)


# def _build_common_message(data):
#     """
#     Construct common notification message.
#     Construct a JSON object that will be used to define the
#     common parts of a notification message that will be sent
#     to any app instance subscribed to the news topic.
#     """
#     return {
#             'notification': {
#                 'title': 'Oppvenuz',
#                 'body': data["message"]
#             },
#             "data": {
#                 "message": data["message"],
#                 "status": data["status"],
#                 "user_id": str(data["user_id"]),
#                 "notification_type": data["notification_type"],
#                 "params": data["params"],
#             }
#         }


class UserListAPI(ListAPIView, CSVDownloadMixin):
    serializer_class = UserDetailSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = (
        "fullname",
        "email",
        "contact_number",
        "role",
        "address_state",
        "address",
    )
    filterset_fields = (
        "address_state",
        "address",
        "status",
    )
    pagination_class = CustomPagination

    def get_queryset(self):
        return CustomUser.objects.filter(role="USER")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.GET.get("download") == "csv":
            return self.download_csv(request, queryset, self.serializer_class)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class VenuesByCityAPIView(ListAPIView):
    serializer_class = CityListSerializer
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ("state__state_name", "city_name")
    filterset_fields = ("is_featured", "is_listed")

    def get_queryset(self):
        cities = (
            VendorService.objects.filter(service_id_id=22, city__isnull=False)
            .values_list("city", flat=True)
            .distinct()
        )
        return City.objects.filter(city_name__in=cities).order_by("city_name")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserAuthView(CreateAPIView):
    """
    Auth View
    """

    serializer_class = None
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserAuthView, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        email_or_phone = request.data.pop("email_or_phone")
        is_email = request.data.pop("is_email")
        if is_email:
            users = CustomUser.objects.filter(email=email_or_phone)
        else:
            users = CustomUser.objects.filter(contact_number=email_or_phone)

        deleted_users = users.filter(status="DELETED")
        for user in deleted_users:
            if user.role == VENDOR:
                deleted_vendor_service_remove(user)
                user.delete()
            user.delete()
        otp = get_otp()

        # multiple users
        if users.count() > 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email" if is_email else "contact_number"
            self.response_format["message"] = (
                messages.EMAIL_ERROR.format(users.first().role)
                if is_email
                else messages.ERR_MANY_USERS
            )
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        # existing user
        if users.count() == 1:
            user = users.first()
            if user.role == "VENDOR":
                if is_email:
                    message = messages.EMAIL_ERROR.format("Vendor")
                else:
                    message = messages.PHONE_ERROR.format("Vendor")
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = "email_or_phone"
                self.response_format["message"] = message
                return Response(self.response_format)
            if user.status == DELETED:
                user.delete()
                user = CustomUser.objects.create(
                    email=email_or_phone if is_email else None,
                    contact_number=None if is_email else email_or_phone,
                    status="PENDING",
                    role="USER",
                    otp=otp,
                    otp_created_at=datetime.now(),
                )
            user.is_existing_user = is_existing_user(user)
            user.otp = otp
            user.otp_created_at = datetime.now()
            user.save()
        else:
            user = CustomUser.objects.create(
                email=email_or_phone if is_email else None,
                contact_number=None if is_email else email_or_phone,
                status="PENDING",
                role="USER",
                otp=otp,
                otp_created_at=datetime.now(),
            )

        update_user_cart_url(user, request.get_host())
        # send email or sms
        if is_email:
            template_id = constants.USER_REGISTER_TEMPLATE
            data_dict = {"user": user.email, "otp": otp}
            send_email(template_id, user.email, data_dict)
        else:
            message = constants.USER_PHONE_VERIF_TEMPLATE.format(otp)
            send_sms(
                config("TEXT_LOCAL_API_KEY"), user.contact_number, "OPPVNZ", message
            )

        # user = self.serializer_class(user, many=False).data
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = (
            messages.LOGIN_OTP_SENT.format("email")
            if is_email
            else messages.LOGIN_OTP_SENT.format("phone number")
        )
        return Response(self.response_format, status=status.HTTP_200_OK)


class VerifyUserView(CreateAPIView):
    """
    Verify user's otp
    """

    serializer_class = VerifyUserSerializer
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VerifyUserView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_or_phone = serializer.validated_data.get("email_or_phone")
        otp = serializer.validated_data.get("otp")
        expire_otp = serializer.data.get("expire_otp", False)

        user = CustomUser.objects.filter(
            Q(email=email_or_phone) | Q(contact_number=email_or_phone)
        ).first()

        if expire_otp:
            user.reset_otp()
            self.response_format["data"] = []
            self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
            self.response_format["error"] = "OTP"
            self.response_format["message"] = messages.OTP_RESET
            return Response(self.response_format, status=status.HTTP_205_RESET_CONTENT)

        if user.otp == otp and (
            datetime.now() < (user.otp_created_at + timedelta(minutes=5))
        ):
            TrackUserSession.objects.create(
                user=user,
                action='login'
            )
            if user.is_existing_user:
                tokens = get_tokens_for_user(user)
                user = UserDetailSerializer(user, many=False).data
                data = {"token": tokens, "user": user}
            else:
                tokens = get_tokens_for_user(user)
                user = UserDetailSerializer(user, many=False).data
                data = {"token": tokens, "user": user}
            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.OTP_VERIFIED
            return Response(self.response_format, status=status.HTTP_200_OK)
        else:
            self.response_format["data"] = []
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "OTP"
            self.response_format["message"] = messages.OTP_INVALID
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class CreateUserProfileView(CreateAPIView):
    """
    Create user profile view
    """

    serializer_class = CreateProfileSerializer
    permission_classes = ()
    authentication_classes = ()
    queryset = CustomUser.objects.none()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CreateUserProfileView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get("email_or_phone")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        fullname = serializer.validated_data.get("fullname")
        state = serializer.validated_data.get("state")
        city = serializer.validated_data.get("city")
        user = CustomUser.objects.filter(
            Q(email=email_or_phone) | Q(contact_number=email_or_phone)
        ).exclude(status=DELETED)
        user = user.first()
        user.fullname = fullname
        user.state_id = state
        user.city_id = city
        user.status = "ACTIVE"
        user.otp = None
        user.is_existing_user = True
        user.set_address_state()
        user.set_address()
        user.save()

        if user.email:
            template_id = constants.VENDOR_WELCOME_TEMPLATE
            data_dict = {"user": user.fullname}
            send_email(template_id, user.email, data_dict)

        tokens = get_tokens_for_user(user)
        user = UserDetailSerializer(user, many=False).data
        data = {"token": tokens, "user": user}
        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = [messages.ADDED.format("User")]
        return Response(self.response_format, status=status.HTTP_201_CREATED)


class UserSignUpAPIView(CreateAPIView):
    """
    Class for creating API view for user registration.
    """

    authentication_classes = ()
    permission_classes = ()
    serializer_class = UserSignUpSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserSignUpAPIView, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        email = request.data.get("email", None)
        user_delete(email)
        role = request.data.get("role", None)
        password = request.data.get("password", None)

        if CustomUser.objects.filter(email=email).exists():
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = [
                messages.EMAIL_ERROR.format(
                    CustomUser.objects.filter(email=email).first().role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        else:
            if serializer.is_valid(raise_exception=True):
                user_id = serializer.save()
                obj = CustomUser.objects.exclude().get(email=request.data["email"])
                jwt_token = get_tokens_for_user(obj)
                url = update_user_cart_url(obj, request.get_host())
                data = {
                    "id": user_id.id,
                    "token": jwt_token,
                    "role": obj.role,
                    "email": obj.email,
                    "fullname": obj.fullname,
                    "image": obj.image,
                    "status": obj.status,
                    "address": obj.address,
                    "address_state": obj.address_state,
                    "contact_number": obj.contact_number,
                    "payment_status": obj.payment_status,
                    "cart_url": obj.cart_url,
                }
                ids = request.data["service_id"]
                for service_id in ids:
                    request.data["vendor_id"] = user_id.id
                    request.data["service_id"] = service_id
                    serialized = AddVendorServiceSerializers(data=request.data)

                    if serialized.is_valid(raise_exception=True):
                        serialized.save()

                template_id = constants.VENDOR_WELCOME_TEMPLATE
                data_dict = {"user": obj.fullname}
                send_email(template_id, obj.email, data_dict)
                if obj.contact_number:
                    # send sms
                    try:
                        message = messages.VENDOR_REC_ON_SIGNUP.format(obj.fullname)
                        resp = send_sms(
                            config("TEXT_LOCAL_API_KEY"),
                            obj.contact_number,
                            "OPPVNZ",
                            message,
                        )
                    except Exception as e:
                        print("Error", e)

                """"
                template_id = "d-f31d699a4f884c4ea595b99e27a54bf3"
                sender = DEFAULT_FROM_EMAIL
                data_dict = {"user_name": obj.fullname}
                ForgotPasswordRequestView.send_mail(self, template_id, sender, obj.email, data_dict)
                """
            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Signup successful."
            return Response(self.response_format)


class SuperUserSignUpAPIView(CreateAPIView):
    """
    Class for creating API view for super user registration.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsSuperAdmin,)
    serializer_class = SuperUserSignUpSerializer

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(SuperUserSignUpAPIView, self).__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)       
        email = request.data.get("email", "").strip().lower()
        user_delete(email)       
        if CustomUser.objects.filter(email__iexact=email).exists():
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = [
                messages.EMAIL_ERROR.format(
                    CustomUser.objects.filter(email=email).first().role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        else:
            if serializer.is_valid(raise_exception=True):
                user_id = serializer.save()                
                obj = CustomUser.objects.exclude().get(email=email)
                data = {
                    "id": user_id.id,
                    "role": obj.role,
                    "email": obj.email,
                    "fullname": obj.fullname,
                    "status": obj.status,
                    "contact_number": obj.contact_number,
                }

                # template_id = constants.WELCOME_TEMPLATE
                # data_dict = {"user_name": obj.fullname}
                # send_email(template_id, obj.email, data_dict)
                # if obj.contact_number:
                #     #send sms
                #     try:
                #         message = messages.REGISTRATION_SMS.format(obj.fullname)
                #         resp = send_sms(os.getenv('TEXT_LOCAL_API_KEY'), obj.contact_number, 'OPPVNZ', message)
                #     except Exception as e:
                #         print("Error", e)

            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            self.response_format["message"] = "Super user signup successful."
            return Response(self.response_format)


class UpgradeOrDowngradeAPIView(APIView):
    """
    Class for updating an existing user to an admin or downgrading to a regular user.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsSuperAdmin,)

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(UpgradeOrDowngradeAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("id", None)
        action = request.data.get("action", None)  # No default action

        if not action:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "missing_action"
            self.response_format["message"] = "Action parameter is required."
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.filter(id=user_id).first()

        if not user:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "user_not_found"
            self.response_format["message"] = "User not found."
            return Response(self.response_format, status=status.HTTP_404_NOT_FOUND)

        if user.is_admin or user.is_superuser:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "invalid_user"
            self.response_format["message"] = (
                "Action cannot be performed on admin or superuser."
            )
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        if action == "upgrade":
            user.is_active = True
            user.is_staff = True
            user.status = "ACTIVE"
        elif action == "downgrade":
            user.is_staff = False
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "invalid_action"
            self.response_format["message"] = "Invalid action provided."
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        user.save()

        data = {
            "id": user.id,
            "role": user.role,
            "email": user.email,
            "fullname": user.fullname,
            "status": user.status,
            "contact_number": user.contact_number,
        }

        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = f"User {action}d successfully."
        return Response(self.response_format, status=status.HTTP_200_OK)


class SearchUserAPIView(APIView):
    """
    Class for searching users based on email, contact number, or fullname.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsSuperAdmin,)

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(SearchUserAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", None)
        contact_number = request.data.get("contact_number", None)
        fullname = request.data.get("fullname", None)

        if email:
            users = CustomUser.objects.filter(
                email__icontains=email, is_superuser=False, is_admin=False
            )
        elif contact_number:
            users = CustomUser.objects.filter(
                contact_number__icontains=contact_number,
                is_superuser=False,
                is_admin=False,
            )
        elif fullname:
            users = CustomUser.objects.filter(
                fullname__icontains=fullname, is_superuser=False, is_admin=False
            )
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "search_parameter"
            self.response_format["message"] = "No search parameter provided."
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        if not users.exists():
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "user_not_found"
            self.response_format["message"] = "No users found."
            return Response(self.response_format, status=status.HTTP_404_NOT_FOUND)

        data = [
            {
                "id": user.id,
                "role": user.role,
                "email": user.email,
                "fullname": user.fullname,
                "contact_number": user.contact_number,
                "is_staff": user.is_staff,
            }
            for user in users
        ]

        self.response_format["data"] = data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = "Users found successfully."
        return Response(self.response_format, status=status.HTTP_200_OK)


class AdminUserDeleteAPIView(APIView):
    """
    Class for creating API view for deleting an admin user.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsSuperAdmin,)

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {
                    "error": "user_id",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "message": ["User ID is required."],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(CustomUser, id=user_id)

        if user.role != "SUPER_ADMIN":
            return Response(
                {
                    "error": "role",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "message": ["Only SUPER_ADMIN users can be deleted."],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_superuser:
            return Response(
                {
                    "error": "role",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "data": None,
                    "message": ["user can not be deleted."],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(
            {
                "status_code": status.HTTP_204_NO_CONTENT,
                "message": "Admin user deleted successfully.",
            },
            status=status.HTTP_204_NO_CONTENT,
        )


class UserLoginAPIView(GenericAPIView):
    """
    Class for creating API view for user login.
    """

    authentication_classes = ()
    permission_classes = ()
    serializer_class = UserLoginSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserLoginAPIView, self).__init__(**kwargs)

    def generate_fcm_token(self, u_id, data, user=False):
        push_objects = FCMDevice.objects.filter(user_id=u_id)

        for notification in push_objects:
            message = Message(
                notification=NotificationSend(title="Oppvenuz", body=data["message"]),
                data={
                    "message": data["message"],
                    "status": data["status"],
                    "user_id": str(data["user_id"]),
                    "notification_type": data["notification_type"],
                    "params": data["params"],
                },
                #  android=AndroidConfig(
                #     ttl=datetime.timedelta(seconds=3600),
                #     priority='high',
                #     notification=AndroidNotification(
                #         channel_id="Oppvenuz-channel"
                #     ),
                # ),
            )

            try:
                if user:
                    notification.send_message(
                        message, app=settings.FIREBASE_MESSAGING_APP
                    )
                else:
                    notification.send_message(message)
            except Exception as e:
                print(f"Error: {e}")

    def post(self, request, *args, **kwargs):
        """
        Function for validating and logging in the user if valid.
        """
        user_type = request.data.get("user_type")
        if CustomUser.objects.filter(email__iexact=request.data["email"]).exclude(
            status=DELETED
        ).exists():           
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.user
                obj = user
                if user_type == "SUPER_ADMIN":
                    if not obj.is_superuser and not obj.is_admin and not obj.is_staff:
                        self.response_format["status_code"] = (
                            status.HTTP_400_BAD_REQUEST
                        )
                        self.response_format["error"] = "login_error"
                        self.response_format["message"] = (
                            "This user is not authorized to this app."
                        )
                        return Response(
                            self.response_format, status=status.HTTP_400_BAD_REQUEST
                        )
                    else:
                        if obj.is_superuser or obj.is_admin or obj.is_staff:
                            jwt_token = get_tokens_for_user(obj)
                            data = {
                                "id": obj.id,
                                "token": jwt_token,
                                "role": "SUPER_ADMIN",  # Temp fix
                                "email": obj.email,
                                "fullname": obj.fullname,
                                "image": obj.image,
                                "status": obj.status,
                                "address_state": obj.address_state,
                                "address": obj.address,
                                "contact_number": obj.contact_number,
                                "payment_status": obj.payment_status,
                            }
                            roles = AdminRoles.objects.filter(
                                user_id=obj.id
                            ).select_related("role_id")
                            roles_data = [role.role_id.role_name for role in roles]
                            if obj.is_admin or obj.is_superuser:
                                roles_data.append("USER_MASTER")
                            data.update({"roles": roles_data})
                            self.response_format["data"] = data
                            self.response_format["message"] = "Login successful."
                            return Response(self.response_format)

                if user_type == obj.role:
                    jwt_token = get_tokens_for_user(obj)
                    data = {
                        "id": obj.id,
                        "token": jwt_token,
                        "role": obj.role,
                        "email": obj.email,
                        "fullname": obj.fullname,
                        "image": obj.image,
                        "status": obj.status,
                        "address_state": obj.address_state,
                        "address": obj.address,
                        "contact_number": obj.contact_number,
                        "payment_status": obj.payment_status,
                    }
                    if obj.role == "VENDOR":
                        is_waved_off = False
                        is_waved_off_count = VendorService.objects.filter(
                            vendor_id=obj.id, is_waved_off=True
                        ).count()
                        if is_waved_off_count > 0:
                            is_waved_off = True
                        data.update({"is_waved_off": is_waved_off})
                    if obj.status == "SUSPENDED":
                        self.response_format["status_code"] = (
                            status.HTTP_400_BAD_REQUEST
                        )
                        self.response_format["error"] = "status"
                        self.response_format["message"] = "You have been suspended."
                    elif obj.status == "DELETED":
                        self.response_format["status_code"] = (
                            status.HTTP_400_BAD_REQUEST
                        )
                        self.response_format["error"] = "status"
                        self.response_format["message"] = (
                            "You have been removed from the platform."
                        )
                    else:
                        self.response_format["data"] = data
                        self.response_format["message"] = "Login successful."
                else:
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = "login_error"
                    self.response_format["message"] = (
                        "This user is not authorized to this app."
                    )
        else:
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "status"
            self.response_format["message"] = messages.UNAUTHORIZED_ACCOUNT
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.response_format)


class ListAdminUsersView(ListAPIView):
    """
    Class for listing all the admin users. role = 'SUPER_ADMIN'
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ListAdminUsersSerializer

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(ListAdminUsersView, self).__init__(**kwargs)

    def post(self, request):
        obj = CustomUser.objects.filter(is_staff=True).order_by("id")
        if obj:
            serializer = self.get_serializer(obj, many=True)
            self.response_format["data"] = serializer.data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Admin users listed successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "admin"
            self.response_format["message"] = "No admin users found."
            return Response(self.response_format)


class GetAdminUsersRolesView(ListAPIView):
    """
    Class for listing Admin user roles from AdminRolesMaster and AdminRoles model using user_id.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = GetAdminUserRolesSerializer

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(GetAdminUsersRolesView, self).__init__(**kwargs)

    def post(self, request):
        user_id = request.data.get("user_id")
        obj = AdminRoles.objects.filter(user_id=user_id)
        if obj:
            serializer = self.get_serializer(obj, many=True)
            role_ids = [role["role_id"] for role in serializer.data]
            self.response_format["data"] = role_ids
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Admin users roles listed successfully."
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "admin"
            self.response_format["message"] = "No admin users roles found."
            return Response(self.response_format)


class SaveAdminUserRolesView(APIView):
    """
    Class for saving Admin user roles to AdminRoles model using user_id and list of role_ids.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(SaveAdminUserRolesView, self).__init__(**kwargs)

    def post(self, request):
        serializer = SaveAdminUserRolesSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data["user_id"]
            role_ids = serializer.validated_data["role_ids"]

            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
                self.response_format["error"] = "user_not_found"
                self.response_format["message"] = "User not found."
                return Response(self.response_format, status=status.HTTP_404_NOT_FOUND)

            # Clear existing roles
            AdminRoles.objects.filter(user_id=user_id).delete()

            # Save new roles
            for role_id in role_ids:
                try:
                    role = AdminRolesMaster.objects.get(id=role_id)
                    AdminRoles.objects.create(user_id=user, role_id=role)
                except AdminRolesMaster.DoesNotExist:
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = "role_not_found"
                    self.response_format["message"] = (
                        f"Role with id {role_id} not found."
                    )
                    return Response(
                        self.response_format, status=status.HTTP_400_BAD_REQUEST
                    )

            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Roles saved successfully."
            return Response(self.response_format, status=status.HTTP_200_OK)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "validation_error"
            self.response_format["message"] = serializer.errors
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutAPIView(GenericAPIView):
    """
    Class for creating API view for user logout.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = BlackListSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserLogoutAPIView, self).__init__(**kwargs)

    def post(self, request):
        """
        Function for logging out the user and blacklisting the access token used.
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header:
            key, access_token = auth_header.split(" ")

            if key == "Bearer":
                request.data["token"] = access_token
                serializer = BlackListSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    TrackUserSession.objects.create(
                        user=request.user,
                        action='logout'
                    )
                    serializer.save()
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_200_OK
                    self.response_format["error"] = None
                    self.response_format["message"] = "Logout Successful."
                    return Response(self.response_format)
                return Response(access_token)
        else:
            return Response("Token not found.", status=status.HTTP_403_FORBIDDEN)


# class UserTokenUpdateView(APIView):
#     """
#     Class for creating API view for generating the token after token is expired.

#     This API to get updated jwt token after expiry of the access to get new token
#     """

#     def __init__(self, **kwargs):
#         """
#          Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(UserTokenUpdateView, self).__init__(**kwargs)

#     permission_classes = ()

#     def get(self, request, *args, **kwargs):
#         """
#         Function for generating new token after the expiration of old token.
#         """
#         # get token from authorization Header
#         auth_header = request.META.get('HTTP_AUTHORIZATION')
#         if auth_header:
#             key, old_token = auth_header.split(' ')

#             if key == 'Bearer':
#                 user = jwt.decode(old_token, options={"verify_signature": False})
#                 if user:
#                     user_id = user['user_id']
#                     try:
#                         obj = CustomUser.objects.get(id=user_id)
#                         # generate JWT token for response
#                         new_token = get_tokens_for_user(obj)
#                         data = {
#                             "token": new_token
#                         }
#                         self.response_format["data"] = data
#                         self.response_format["status_code"] = status.HTTP_201_CREATED
#                         self.response_format["error"] = None
#                         return Response(self.response_format)
#                     except CustomUser.DoesNotExist:
#                         return Response("User does not exist in database.")
#                 else:
#                     return Response("JWT decoding error.")
#             else:
#                 return Response("Bearer token not found.")


class UserTokenUpdateView(APIView):
    """
    Class for creating API view for generating the token after token is expired.

    This API allows getting an updated JWT token after expiry of the access token.
    """

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserTokenUpdateView, self).__init__(**kwargs)

    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        Function for generating new token after the expiration of old token.
        """
        # get token from Authorization Header
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            # If no auth header is present, return an error response
            return Response(
                {"error": "Authorization header is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            key, old_token = auth_header.split(" ")
        except ValueError:
            return Response(
                {"error": "Invalid authorization header format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if key != "Bearer":
            return Response(
                {"error": "Bearer token not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Decode the token without verifying the signature
            user_data = jwt.decode(old_token, options={"verify_signature": False})
        except Exception as e:
            return Response(
                {"error": f"JWT decoding error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure user data exists in the decoded token
        if not user_data or "user_id" not in user_data:
            return Response(
                {"error": "Invalid token or user_id missing in token payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = user_data["user_id"]

        try:
            # Retrieve the user from the database
            obj = CustomUser.objects.get(id=user_id)
            # Generate a new JWT token for the user
            new_token = get_tokens_for_user(obj)
            data = {"token": new_token}
            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = None
            return Response(self.response_format, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User does not exist in the database."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ForgotPasswordRequestView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ForgotPasswordSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ForgotPasswordRequestView, self).__init__(**kwargs)

    def post(self, request):
        email = request.data["email"]
        try:
            user = CustomUser.objects.get(email=email)
            if user.status == DELETED:
                self.response_format["data"] = None
                self.response_format["message"] = messages.UNAUTHORIZED_ACCOUNT
                self.response_format["error"] = "email"
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                return Response(self.response_format)

            if user and user.role == "SUPER_ADMIN":
                otp = random.randint(1000, 9999)
                request.data["otp"] = otp
                date = datetime.now()
                request.data["created_at"] = str(date)
                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    generated_email = "/" + email
                    reset_url = FORGOT_PASSWORD_URL + "/" + str(otp) + generated_email

                    # template_id = "d-1772e8ac6b5442e68975394ea71a4957"
                    template_id = constants.FORGOT_PASSWORD_TEMPLATE
                    data_dict = {
                        "user_name": user.fullname.title(),
                        "reset_link": reset_url,
                    }
                    send_email(template_id, email, data_dict)
                    # data_dict = {"user_name": obj.fullname}
                    # send_email(template_id, obj.email, data_dict)
                    # ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)

                    self.response_format["data"] = None
                    self.response_format["error"] = None
                    self.response_format["status_code"] = status.HTTP_200_OK
                    self.response_format["message"] = "Successfully send mail."
                    return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "user"
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["message"] = "User does not exists."
            return Response(self.response_format)
        self.response_format["data"] = None
        self.response_format["error"] = "user"
        self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
        self.response_format["message"] = "This user is not authorized to this app."
        return Response(self.response_format)


class UserForgotPasswordRequestView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ForgotPasswordSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UserForgotPasswordRequestView, self).__init__(**kwargs)

    def post(self, request):
        email = request.data["email"]
        try:
            user = CustomUser.objects.get(email=email)
            if user.status == DELETED:
                self.response_format["data"] = None
                self.response_format["message"] = messages.UNAUTHORIZED_ACCOUNT
                self.response_format["error"] = "email"
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                return Response(self.response_format)

            if user and user.role == "USER":
                otp1 = random.randint(1000, 9999)
                request.data["otp"] = otp1
                current_date = datetime.now()
                request.data["created_at"] = str(current_date)
                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    generated_email = "/" + email
                    reset_url = (
                        USER_FORGOT_PASSWORD_URL + "/" + str(otp1) + generated_email
                    )

                    # template_id = "d-1772e8ac6b5442e68975394ea71a4957"
                    # sender = DEFAULT_FROM_EMAIL
                    # data_dict = {"user_name": user.fullname, "reset_link": reset_url}
                    # ForgotPasswordRequestView.send_mail(self, template_id, sender, email, data_dict)

                    template_id = constants.FORGOT_PASSWORD_TEMPLATE
                    data_dict = {
                        "user_name": user.fullname.title(),
                        "reset_link": reset_url,
                    }
                    send_email(template_id, email, data_dict)

                self.response_format["data"] = None
                self.response_format["message"] = "Successfully send mail."
                self.response_format["error"] = None
                self.response_format["status_code"] = status.HTTP_200_OK
                return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["error"] = "user"
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["message"] = "User does not exists."
            return Response(self.response_format)
        self.response_format["error"] = "user"
        self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
        self.response_format["data"] = None
        self.response_format["message"] = "This user is not authorized to this app."
        return Response(self.response_format)


class VendorForgotPasswordRequestView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ForgotPasswordSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(VendorForgotPasswordRequestView, self).__init__(**kwargs)

    def post(self, request):
        vendor_email = request.data["email"]
        try:
            user = CustomUser.objects.get(email=vendor_email)
            if user.status == DELETED:
                self.response_format["data"] = None
                self.response_format["message"] = messages.UNAUTHORIZED_ACCOUNT
                self.response_format["error"] = "email"
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                return Response(self.response_format)

            if user and user.role == "VENDOR":
                otp = random.randint(1000, 9999)
                request.data["otp"] = otp
                date = datetime.now()
                request.data["created_at"] = str(date)
                serializer = self.get_serializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    generated_email = "/" + vendor_email
                    reset_url = (
                        VENDOR_FORGOT_PASSWORD_URL + "/" + str(otp) + generated_email
                    )

                    # template_id = "d-1772e8ac6b5442e68975394ea71a4957"
                    # sender = DEFAULT_FROM_EMAIL
                    # data_dict = {"user_name": user.fullname, "reset_link": reset_url}
                    # ForgotPasswordRequestView.send_mail(self, template_id, sender, vendor_email, data_dict)

                    template_id = constants.FORGOT_PASSWORD_TEMPLATE
                    data_dict = {
                        "user_name": user.fullname.title(),
                        "reset_link": reset_url,
                    }
                    send_email(template_id, vendor_email, data_dict)

                self.response_format["data"] = None
                self.response_format["error"] = None
                self.response_format["message"] = "Successfully send mail."
                self.response_format["status_code"] = status.HTTP_200_OK
                return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "user"
            self.response_format["message"] = "User does not exists."
            return Response(self.response_format)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
        self.response_format["error"] = "user"
        self.response_format["message"] = "This user is not authorized to this app."
        return Response(self.response_format)


class PasswordResetRequest(UpdateAPIView):
    """
    Class for resetting password against the requested forgot password email.
    """

    authentication_classes = ()
    permission_classes = ()
    serializer_class = UpdateUserPasswordSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(PasswordResetRequest, self).__init__(**kwargs)

    def update(self, request, *args, **kwargs):
        """
        Function for validating and logging in the user if valid.
        """
        data = request.data
        try:
            obj = CustomUser.objects.get(email=data["email"])
            if obj:
                if data["password"] is None or data["confirm_password"] is None:
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = "password"
                    self.response_format["message"] = "Password Should Not be Empty."
                    return Response(self.response_format)
                if data["confirm_password"] != data["password"]:
                    self.response_format["data"] = None
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = "confirm_password"
                    self.response_format["message"] = (
                        "Confirm password should be same as above password."
                    )
                    return Response(self.response_format)
                else:
                    try:
                        forget_password_object = ForgotPasswordRequest.objects.get(
                            email=data["email"]
                        )
                        if forget_password_object:
                            if forget_password_object.request_status == "UU":
                                if data["otp"] != forget_password_object.otp:
                                    self.response_format["data"] = None
                                    self.response_format["status_code"] = (
                                        status.HTTP_404_NOT_FOUND
                                    )
                                    self.response_format["error"] = "otp"
                                    self.response_format["message"] = (
                                        "Link expired. "
                                        "Please use the latest link send on your email."
                                    )
                                    return Response(self.response_format)
                                else:
                                    forget_password_object.request_status = "U"
                                    new_object = {
                                        "email": forget_password_object.email,
                                        "otp": forget_password_object.otp,
                                        "request_status": forget_password_object.request_status,
                                        "created_at": forget_password_object.created_at,
                                    }

                                    forget_password_updated_data = (
                                        ForgotPasswordSerializer(data=new_object)
                                    )
                                    if forget_password_updated_data.is_valid(
                                        raise_exception=True
                                    ):
                                        forget_password_updated_data.save()
                                        new_password_data = {
                                            "email": data["email"],
                                            "password": data["password"],
                                        }
                                        serialized = UpdateUserPasswordSerializer(
                                            instance=obj, data=new_password_data
                                        )
                                        if serialized.is_valid(raise_exception=True):
                                            serialized.save()
                                            self.response_format["data"] = None
                                            self.response_format["status_code"] = (
                                                status.HTTP_200_OK
                                            )
                                            self.response_format["error"] = None
                                            self.response_format["message"] = (
                                                "Password changed successfully."
                                            )
                                            return Response(self.response_format)
                            else:
                                self.response_format["data"] = None
                                self.response_format["status_code"] = (
                                    status.HTTP_400_BAD_REQUEST
                                )
                                self.response_format["error"] = "status"
                                self.response_format["message"] = (
                                    "This link has already been used please"
                                    " generate another request."
                                )
                                return Response(self.response_format)
                    except ForgotPasswordRequest.DoesNotExist:
                        self.response_format["data"] = None
                        self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
                        self.response_format["error"] = "email"
                        self.response_format["message"] = (
                            "No request found for changing the password."
                        )
                        return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "email"
            self.response_format["message"] = "User with this email does not exist."
            return Response(self.response_format)


class ChangePasswordAPIView(UpdateAPIView):
    """
    Class for changing user password.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = ChangePasswordSerializer

    def __init__(self, **kwargs):
        self.response_format = ResponseInfo().response
        super(ChangePasswordAPIView, self).__init__(**kwargs)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)
        new_password = request.data.get("new_password")

        if self.object.role == "VENDOR":
            if not 5 <= len(new_password) <= 16:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = "new_password"
                self.response_format["message"] = messages.PASS_LIMIT
                return Response(self.response_format)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = "old_password"
                self.response_format["message"] = messages.OLD_PASSWORD_WRONG
                return Response(self.response_format)
            # set_password also hashes the password that the user will get
            self.object.set_password(new_password)
            self.object.save()
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.PASSWORD_CHANGED
            return Response(self.response_format)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InviteUserView(GenericAPIView):
    """
    Class for inviting a user on platform.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = InviteUserSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(InviteUserView, self).__init__(**kwargs)

    def post(self, request):
        email = request.data["email"]
        fullname = request.data["fullname"]
        u_type = request.data.get("role")

        if request.META["HTTP_HOST"] == STAGING_API_URL:
            client = dev_client
        elif request.META["HTTP_HOST"] == PROD_API_URL:
            client = staging_client
        else:
            client = dev_client

        response = client.create_deep_link_url(
            data={"user": {"fullname": fullname, "email": email}}, channel="email"
        )

        get_url = response[branchio.RETURN_URL]
        if u_type == "VENDOR":
            url = get_url
        elif u_type == "USER":
            url = get_url
        try:
            CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid(raise_exception=True):
                # template_id = "d-3b7ec5e566a24b8c930d26a23c72c7b3"
                template_id = constants.VENDOR_INVITATION_TEMPLATE
                data_dict = {"vendor_name": fullname, "branch_invite_link": url}
                # send email to vendor
                send_email(template_id, email, data_dict)
                serializer.save()
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Invite sent successfully!"
            return Response(self.response_format)
        else:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = "User already exist in database."
            return Response(self.response_format)


class UpdateUserViewOld(UpdateAPIView):
    """
    Class for updating user's profile.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UpdateUserSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserViewOld, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_id = self.kwargs["pk"]
        return CustomUser.objects.filter(id=user_id)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.fullname = request.data.get("fullname")
        instance.email = request.data.get("email")
        instance.contact_number = request.data.get("contact_number")
        instance.image = request.data.get("image")
        instance.address = request.data.get("address")
        instance.address_state = request.data.get("address_state", None)
        instance.status = request.data.get("status")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            self.response_format["data"] = serializer.data
            self.response_format["error"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["message"] = messages.UPDATE.format("The profile")
        return Response(self.response_format)


class UpdateUserView(UpdateAPIView):
    """
    Class for updating user's profile.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UserDetailSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_id = self.kwargs["pk"]
        return CustomUser.objects.filter(id=user_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        contact_number = request.data.get("contact_number", None)
        users = CustomUser.objects.filter(contact_number=contact_number).exclude(
            id=instance.id
        )
        if users.exists():
            self.response_format["data"] = None
            self.response_format["error"] = "contact_number"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = messages.PHONE_ERROR.format(
                users.first().role
            )
            return Response(self.response_format)

        user_status = request.data.get("status", None)
        reason = request.data.get("reason", None)

        if user_status != "ACTIVE" and not reason:
            self.response_format["data"] = None
            self.response_format["error"] = "reason"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = messages.ENQ_REASON
            return Response(self.response_format)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        self.response_format["data"] = serializer.data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.UPDATE.format("The profile")
        return Response(self.response_format)


class GetUserDetailAPIViewOld(ListAPIView):
    """
    Class for getting user's profile details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UserSignUpSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetUserDetailAPIViewOld, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()

    def post(self, request, *args, **kwargs):
        obj = CustomUser.objects.filter(email=request.data["email"])
        data = {
            "id": obj[0].id,
            "role": obj[0].role,
            "email": obj[0].email,
            "fullname": obj[0].fullname,
            "image": obj[0].image,
            "status": obj[0].status,
            "address": obj[0].address,
            "address_state": obj[0].address_state,
            "contact_number": obj[0].contact_number,
        }
        self.response_format["data"] = data

        return Response(self.response_format)


class GetUserDetailAPIView(ListAPIView):
    """
    Class for getting user's profile details.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UserDetailSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetUserDetailAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()

    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get("email_or_phone", None)
        is_email = request.data.get("is_email", False)

        try:
            if is_email:
                user = CustomUser.objects.get(email=email_or_phone)
            else:
                user = CustomUser.objects.get(contact_number=email_or_phone)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "email_or_phone"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = messages.NOT_FOUND.format("user")
            return Response(self.response_format)
        except CustomUser.MultipleObjectsReturned:
            self.response_format["data"] = None
            self.response_format["error"] = "email_or_phone"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = messages.ERR_MANY_USERS
            return Response(self.response_format)

        data = UserDetailSerializer(user, many=False).data
        self.response_format["data"] = data
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


# class GetUserDetailAPIView(ListAPIView):
#     """
#     Class for getting user's profile details.
#     """
#     permission_classes = (IsAuthenticated, IsTokenValid)
#     authentication_classes = (OAuth2Authentication, JWTAuthentication)
#     serializer_class = UserDetailSerializer

#     def __init__(self, **kwargs):
#         """
#          Constructor function for formatting the web response to return.
#         """
#         self.response_format = ResponseInfo().response
#         super(GetUserDetailAPIView, self).__init__(**kwargs)

#     def get_queryset(self):
#         if getattr(self, 'swagger_fake_view', False):
#             return CustomUser.objects.none()

#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email', None)
#         try:
#             user = CustomUser.objects.get(email=email)
#         except CustomUser.DoesNotExist:
#             self.response_format["data"] = None
#             self.response_format["error"] = "email"
#             self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
#             self.response_format["message"] = messages.NOT_FOUND.format('user')
#             return Response(self.response_format)

#         data = UserDetailSerializer(user, many=False).data
#         self.response_format["data"] = data
#         self.response_format["error"] = None
#         self.response_format["status_code"] = status.HTTP_200_OK
#         self.response_format["message"] = messages.SUCCESS
#         return Response(self.response_format)


# data = {
#     "id": obj[0].id,
#     "role": obj[0].role,
#     "email": obj[0].email,
#     "fullname": obj[0].fullname,
#     "image": obj[0].image,
#     "status": obj[0].status,
#     "address": obj[0].get_address,
#     "address_state": obj[0].get_address_state,
#     "contact_number": obj[0].contact_number
# }
# self.response_format["data"] = data

# return Response(self.response_format)


class UpdateUserStatusViewOld(UpdateAPIView, DestroyAPIView):
    """
    Class for updating a user status.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = UpdateUserStatusSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserStatusViewOld, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_id = self.kwargs["pk"]
        return CustomUser.objects.filter(id=user_id)

    def post(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get("status")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            if request.data.get("status") == DELETED and instance.role == VENDOR:
                deleted_vendor_service_remove(instance)
            self.response_format["data"] = serializer.data
            self.response_format["message"] = messages.DELETE.format("Account")

        return Response(self.response_format)


class UpdateUserStatusView(UpdateAPIView, DestroyAPIView):
    """
    Class for updating a user status.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = UpdateUserStatusSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateUserStatusView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()
        user_id = self.kwargs["pk"]
        return CustomUser.objects.filter(id=user_id)

    def post(self, request, pk, *args, **kwargs):
        instance = self.get_object()
        instance.status = request.data.get("status")

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.partial_update(serializer)
            if request.data.get("status") == DELETED:
                instance.set_is_existing_user(flag=False)
                if instance.role == VENDOR:
                    deleted_vendor_service_remove(instance)
            self.response_format["data"] = serializer.data
            self.response_format["message"] = messages.DELETE.format("Account")
        return Response(self.response_format)


class GenerateEmailVerificationView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = EmailVerificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GenerateEmailVerificationView, self).__init__(**kwargs)

    def post(self, request):
        email = request.data["email"]
        if CustomUser.objects.filter(email=email).exists():
            user_delete(email)
        try:
            CustomUser.objects.get(email=email)
            self.response_format["data"] = None
            self.response_format["error"] = "email"
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["message"] = (
                f"Email already used with other {CustomUser.objects.get(email=email).role} role."
            )
            return Response(self.response_format)
        except CustomUser.DoesNotExist:
            otp = random.randint(100000, 999999)
            request.data["secret_code"] = otp
            request.data["is_verified"] = False
            date = datetime.now()
            request.data["created_at"] = str(date)
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            # template_id = "d-9e2fba5cb85c4666b0a06e2ca7700705"
            template_id = constants.VENDOR_EMAIL_VERIFICATION_TEMPLATE
            data_dict = {"user": email, "otp": otp}
            send_email(template_id, email, data_dict)

            self.response_format["data"] = None
            self.response_format["error"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["message"] = "Email sent successfully."
            return Response(self.response_format)


class ValidateEmailVerificationView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = EmailVerificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ValidateEmailVerificationView, self).__init__(**kwargs)

    def post(self, request):
        email = request.data["email"]
        secret_code = request.data["secret_code"]
        try:
            email_id = EmailVerification.objects.filter(email=email).values_list(
                "email", "secret_code", "created_at"
            )
            # print("Email", email_id, type(email_id))
            td = datetime.now() - email_id[0][2]
            days = td.days
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days == 0 and minutes < 5:
                if int(secret_code) == (email_id[0][1]):
                    EmailVerification.objects.filter(email=email).update(
                        is_verified=True
                    )
                    self.response_format["message"] = "Verification successful."
                else:
                    self.response_format["error"] = "invalid_otp"
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["message"] = (
                        "Email verification code is invalid."
                    )
            else:
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["message"] = (
                    "Email verification code is expired. Please generate new verification code."
                )
            return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "email"
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["message"] = "Email does not exists."
            return Response(self.response_format)


class GeneratePhoneVerificationViewOld(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = PhoneVerificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GeneratePhoneVerificationViewOld, self).__init__(**kwargs)

    def post(self, request):
        phone_number = request.data["phone_number"]
        type(phone_number)
        otp = random.randint(100000, 999999)
        request.data["secret_code"] = otp
        request.data["is_verified"] = False
        date = datetime.now()
        request.data["created_at"] = str(date)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        # content1 = "Hi, Your mobile verification OTP is "
        # wishes = "\nThanks,\nThe OppVenuz Team."
        # message = content1 + str(otp) + wishes
        message = constants.PHONE_VERIFICATION_MSG_TEMPLATE.format(otp)
        resp = send_sms(config("TEXT_LOCAL_API_KEY"), phone_number, "OPPVNZ", message)
        self.response_format["data"] = None
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = "Message sent successfully."
        return Response(self.response_format)


class GeneratePhoneVerificationView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = PhoneVerificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GeneratePhoneVerificationView, self).__init__(**kwargs)

    def post(self, request):
        phone_number = request.data["phone_number"]
        users = CustomUser.objects.filter(contact_number=phone_number)

        deleted_users = users.filter(status=DELETED)
        for user in deleted_users:
            if user.role == VENDOR:
                deleted_vendor_service_remove(user)
                user.delete()
            else:
                user.delete()

        if users.count() > 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "contact_number"
            self.response_format["message"] = [messages.ERR_MANY_USERS]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        if users.count() == 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "contact_number"
            self.response_format["message"] = [
                messages.PHONE_ERROR.format(
                    CustomUser.objects.filter(contact_number=phone_number)
                    .first()
                    .role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        type(phone_number)
        otp = random.randint(100000, 999999)
        request.data["secret_code"] = otp
        request.data["is_verified"] = False
        date = datetime.now()
        request.data["created_at"] = str(date)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        # content1 = "Hi, Your mobile verification OTP is "
        # wishes = "\nThanks,\nThe OppVenuz Team."
        # message = content1 + str(otp) + wishes
        message = constants.PHONE_VERIFICATION_MSG_TEMPLATE.format(otp)
        resp = send_sms(config("TEXT_LOCAL_API_KEY"), phone_number, "OPPVNZ", message)
        self.response_format["data"] = None
        self.response_format["error"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["message"] = "Message sent successfully."
        return Response(self.response_format)


class ValidatePhoneVerificationView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = EmailVerificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ValidatePhoneVerificationView, self).__init__(**kwargs)

    def post(self, request):
        phone_number = request.data["phone_number"]
        secret_code = request.data["secret_code"]
        try:
            phone_number_id = PhoneVerification.objects.filter(
                phone_number=phone_number
            ).values_list("phone_number", "secret_code", "created_at")
            # print("Phone Number", phone_number_id, type(phone_number_id))
            td = datetime.now() - phone_number_id[0][2]
            days = td.days
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days == 0 and minutes < 5:
                if int(secret_code) == (phone_number_id[0][1]):
                    PhoneVerification.objects.filter(phone_number=phone_number).update(
                        is_verified=True
                    )
                    self.response_format["message"] = "Verification successful."
                else:
                    self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                    self.response_format["error"] = "invalid_otp"
                    self.response_format["message"] = "Invalid OTP."
            else:
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["message"] = "OTP expired please generate new OTP."
            return Response(self.response_format)
        except CustomUser.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["error"] = "phone_number"
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["message"] = "Phone number does not exists."
            return Response(self.response_format)


class GetStateListView(ListAPIView):

    permission_classes = ()
    authentication_classes = ()
    serializer_class = StateSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetStateListView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return State.objects.none()

    def get(self, request):
        """
        Function for getting state list.
        Authorization Header required.
        """
        if request.query_params.get("is_listed", False):
            state_ids = cities = (
                City.objects.filter(is_listed=True)
                .values_list("state", flat=True)
                .distinct()
            )
            state_list = State.objects.filter(id__in=state_ids)
        else:
            state_list = State.objects.all().order_by("state_name")
        state_list_serialized = self.get_serializer(state_list, many=True)

        self.response_format["data"] = state_list_serialized.data

        return Response(self.response_format)


class GetCityListView(ListAPIView):
    """
    Class for creating API view for getting city list.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = CitySerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ("is_listed", "is_featured")
    search_fields = ("city_name",)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetCityListView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return City.objects.none()

    def get(self, request):
        """
        Function for getting city list.
        Authorization Header required.
        """

        city_list = City.objects.all().order_by("city_name")
        state_name = self.request.GET.get("state_name", None)
        if state_name:
            city_list = city_list.filter(state__state_name=state_name)
        city_list_serialized = self.get_serializer(
            self.filter_queryset(city_list), many=True
        )

        self.response_format["data"] = city_list_serialized.data

        return Response(self.response_format)


class GetNotificationListView(ListAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = NotificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetNotificationListView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()

    def generate_notification_data(
        self, notification_result, notification_unread_count
    ):
        data = list()
        for notification in notification_result:
            data.append(
                {
                    "id": notification.id,
                    "message": notification.message,
                    "status": notification.status,
                    "notification_type": notification.notification_type,
                    "params": json.loads(notification.params),
                    "created_at": notification.created_at,
                    "unread_count": notification_unread_count,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """
        Function for retrieving notification list.
        Authorization Header required.
        """
        try:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            notification_result = Notification.objects.filter(
                user_id=request.user
            ).order_by("-created_at")
            notification_unread_count = Notification.objects.filter(
                user_id=request.user, status="UR"
            ).count()
            data = GetNotificationListView.generate_notification_data(
                self, notification_result, notification_unread_count
            )
            result_users = paginator.paginate_queryset(data, request)
            return CustomPagination.get_paginated_response(paginator, result_users)
        except Notification.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "id"
            self.response_format["message"] = "Notification not available."
            return Response(self.response_format)


class GetApplicationDetailAPIView(ListAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = ApplicationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetApplicationDetailAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()

    def get(self, request, *args, **kwargs):
        """
        Function for retrieving notification list.
        Authorization Header required.
        """
        result = Application.objects.all().first()
        serialized_result = self.get_serializer(result)

        self.response_format["data"] = serialized_result.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = ["Success."]
        return Response(self.response_format)


class UpdateNotificationStatusView(UpdateAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = NotificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(UpdateNotificationStatusView, self).__init__(**kwargs)

    def get_queryset(self):
        """
        This view should return a notification by its id.
        """
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        notification_id = self.kwargs["pk"]
        return Notification.objects.filter(id=notification_id)

    def put(self, request, *args, **kwargs):
        self.partial_update(request, *args, **kwargs)
        self.response_format["data"] = []
        return Response(self.response_format)


class SendContactUsAPIView(GenericAPIView):
    """
    Class for inviting a user on platform.
    """

    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = InviteUserSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(SendContactUsAPIView, self).__init__(**kwargs)

    def post(self, request):
        user = request.user

        # template_id = "d-694061e3ab774807aed2ad0eda8d85b8"
        template_id = constants.VENDOR_FILLED_CONTACT_US_TEMPLATE
        sender = DEFAULT_FROM_EMAIL
        data_dict = {
            "vendor_name": user.fullname,
            "vendor_email": user.email,
            "user_phone": user.contact_number,
            "vendor_message": request.data["sender_message"],
        }
        send_email(template_id, sender, data_dict, bcc=True)

        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.CONTACT_FORM_SUBMIT
        return Response(self.response_format)


class FCMDeviceViewSet(CreateAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)
    serializer_class = FCMSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(FCMDeviceViewSet, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        serialized = self.get_serializer(data=request.data)
        FCMDevice.objects.filter(
            user_id=request.user.id, device_id=request.data["device_id"]
        ).delete()
        if serialized.is_valid(raise_exception=True):
            serialized.save(user_id=request.user.id)
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_201_CREATED
            self.response_format["error"] = "fcm"
            self.response_format["message"] = "Device registered."
            return Response(self.response_format)


class DeleteFCMDeviceViewSet(DestroyAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = FCMSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(DeleteFCMDeviceViewSet, self).__init__(**kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = FCMDevice.objects.filter(device_id=request.data["device_id"])
        self.perform_destroy(instance)

        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = "fcm"
        self.response_format["message"] = "Device deleted."
        return Response(self.response_format)


class ClearAllAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = NotificationSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(ClearAllAPIView, self).__init__(**kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Function for retrieving User list.
        Authorization Header required.
        """
        try:
            notification_result = Notification.objects.filter(user_id=request.user)
            for notification in notification_result:
                notification.delete()
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = "Notification cleared successfully."
            return Response(self.response_format)
        except Notification.DoesNotExist:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_404_NOT_FOUND
            self.response_format["error"] = "user_id"
            self.response_format["message"] = "Notfication does not found."
            return Response(self.response_format)


class AddVendorAPIViewOld(CreateAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = AddVendorSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorAPIViewOld, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        serialized = self.get_serializer(data=request.data)
        email = request.data.get("email", None)
        user_delete(email)
        if CustomUser.objects.filter(email=email).exists():
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = [
                messages.EMAIL_ERROR.format(
                    CustomUser.objects.filter(email=email).first().role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        else:
            password = generate_password()
            if serialized.is_valid(raise_exception=True):
                vendor_obj = serialized.save()
                vendor_obj.set_password(password)
                vendor_obj.save()
                ids = request.data["service_id"]

                for service_id in ids:
                    request.data["vendor_id"] = vendor_obj.id
                    request.data["service_id"] = service_id
                    serialized = AddVendorServiceSerializers(data=request.data)

                    if serialized.is_valid(raise_exception=True):
                        serialized.save()
                template_id = ADMIN_VENDOR_REGISTRATION_TEMPLATE
                data_dict = {
                    "user_name": vendor_obj.fullname,
                    "email": vendor_obj.email,
                    "password": password,
                }
                send_email(template_id, vendor_obj.email, data_dict, bcc=True)
                template_id = ADMIN_REC_WHEN_VENDOR_REG_BY_ADMIN
                data_dict = {
                    "vendor_name": vendor_obj.fullname,
                    "vendor_email": vendor_obj.email,
                    "vendor_phone": vendor_obj.contact_number,
                }
                send_email(template_id, request.user.email, data_dict, bcc=True)

                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_201_CREATED
                self.response_format["error"] = None
                self.response_format["message"] = messages.ADDED.format("Vendor")
                return Response(self.response_format)
            else:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = serialized.errors
                self.response_format["message"] = messages.ERROR.format(
                    "Vendor Register"
                )
                return Response(self.response_format)


class AddVendorAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated, IsTokenValid)
    authentication_classes = (JWTAuthentication,)
    serializer_class = AddVendorSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddVendorAPIView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        serialized = self.get_serializer(data=request.data)
        email = request.data.get("email", None)
        contact_number = request.data.get("contact_number", None)

        users = CustomUser.objects.filter(contact_number=contact_number)

        deleted_users = users.filter(status=DELETED)
        for user in deleted_users:
            if user.role == VENDOR:
                deleted_vendor_service_remove(user)
                user.delete()
            user.delete()

        user_delete(email)

        if users.count() > 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "contact_number"
            self.response_format["message"] = [messages.ERR_MANY_USERS]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        if users.count() == 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "contact_number"
            self.response_format["message"] = [
                messages.PHONE_ERROR.format(
                    CustomUser.objects.filter(contact_number=contact_number)
                    .first()
                    .role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=email).exists():
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = [
                messages.EMAIL_ERROR.format(
                    CustomUser.objects.filter(email=email).first().role.lower()
                )
            ]
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)
        else:
            password = generate_password()
            if serialized.is_valid(raise_exception=True):
                vendor_obj = serialized.save()
                vendor_obj.set_password(password)
                vendor_obj.save()
                ids = request.data["service_id"]

                for service_id in ids:
                    request.data["vendor_id"] = vendor_obj.id
                    request.data["service_id"] = service_id
                    serialized = AddVendorServiceSerializers(data=request.data)

                    if serialized.is_valid(raise_exception=True):
                        serialized.save()
                template_id = ADMIN_VENDOR_REGISTRATION_TEMPLATE
                data_dict = {
                    "user_name": vendor_obj.fullname,
                    "email": vendor_obj.email,
                    "password": password,
                }
                send_email(template_id, vendor_obj.email, data_dict, bcc=True)
                template_id = ADMIN_REC_WHEN_VENDOR_REG_BY_ADMIN
                data_dict = {
                    "user": vendor_obj.fullname,
                    "email": vendor_obj.email,
                    "contact_number": vendor_obj.contact_number,
                }
                send_email(template_id, request.user.email, data_dict, bcc=True)

                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_201_CREATED
                self.response_format["error"] = None
                self.response_format["message"] = messages.ADDED.format("Vendor")
                return Response(self.response_format)
            else:
                self.response_format["data"] = None
                self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
                self.response_format["error"] = serialized.errors
                self.response_format["message"] = messages.ERROR.format(
                    "Vendor Register"
                )
                return Response(self.response_format)


class GetUserDetailView(GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = UserSignUpSerializer

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(GetUserDetailView, self).__init__(**kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomUser.objects.none()

    def post(self, request, *args, **kwargs):
        obj = CustomUser.objects.exclude().get(id=request.data["user_id"])
        data = {
            "id": obj.id,
            "role": obj.role,
            "email": obj.email,
            "fullname": obj.fullname,
            "image": obj.image,
            "status": obj.status,
            "address": obj.address,
            "address_state": obj.address_state,
            "contact_number": obj.contact_number,
            "payment_status": obj.payment_status,
        }
        self.response_format["data"] = data
        return Response(self.response_format)


"""
from rest_framework_social_oauth2.views import TokenView

class MyTokenView(TokenView):

    def post(self, request, *args, **kwargs):
        response = super(MyTokenView, self).post(request, *args, **kwargs)
        return Response({
            'status': Your_Status,
            'data': response.data,
        }, status=response.status_code)
"""


class AddCityView(CreateAPIView):
    """
    Add new city to table
    """

    serializer_class = CityDetailSerializer
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AddCityView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = messages.SUCCESS
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_201_CREATED)


class CityUpdateAPIView(UpdateAPIView):
    serializer_class = CityListSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    http_method_names = ("patch", "put")

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(CityUpdateAPIView, self).__init__(**kwargs)

    def get_queryset(self):
        return City.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_205_RESET_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.UPDATE.format("Banner")
        return Response(self.response_format)


class AppleSinInView(CreateAPIView):
    permission_classes = ()
    authentication_classes = ()

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(AppleSinInView, self).__init__(**kwargs)

    def post(self, request, *args, **kwargs):
        token = request.data.get("identity_token", None)
        fullname = request.data.get("fullname", None)

        if not token or not fullname:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "token or fullname"
            self.response_format["message"] = messages.TOKEN_OR_NAME
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["RS256"],
                audience="https://appleid.apple.com",
                issuer=f"https://appleid.apple.com/{SOCIAL_AUTH_APPLE_ID_TEAM}",
            )
        except jwt.ExpiredSignatureError:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "token"
            self.response_format["message"] = messages.ID_TOKEN_EXPIRED
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        except jwt.InvalidTokenError:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "token"
            self.response_format["message"] = messages.ID_TOKEN_EXPIRED
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)

        email = result.get("email")

        users = CustomUser.objects.filter(email=email)
        users.filter(status=DELETED).delete()
        if users.count() == 1:
            user = users.first()
            tokens = get_tokens_for_user(user)
            update_user_cart_url(user, request.get_host())
            data = {
                "token": tokens,
                "expires_in": 36000,
                "scope": "read write",
                "token_type": "Bearer",
            }
            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.SUCCESS
            return Response(self.response_format, status=status.HTTP_200_OK)

        if users.count() == 0:
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={"fullname": fullname, "role": "USER", "status": "ACTIVE"},
            )
            tokens = get_tokens_for_user(user)
            update_user_cart_url(user, request.get_host())
            data = {
                "token": tokens,
                "expires_in": 36000,
                "scope": "read write",
                "token_type": "Bearer",
            }
            self.response_format["data"] = data
            self.response_format["status_code"] = status.HTTP_200_OK
            self.response_format["error"] = None
            self.response_format["message"] = messages.SUCCESS
            return Response(self.response_format, status=status.HTTP_200_OK)

        if users.count() > 1:
            self.response_format["data"] = None
            self.response_format["status_code"] = status.HTTP_400_BAD_REQUEST
            self.response_format["error"] = "email"
            self.response_format["message"] = messages.ERR_MANY_USERS
            return Response(self.response_format, status=status.HTTP_400_BAD_REQUEST)


class DeleteUsersOnNumberOrEmail(CreateAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = UserDetailSerializer
    queryset = CustomUser.objects.all()

    def create(self, request, *args, **kwargs):
        email_or_phone = request.data.get("email_or_phone", None)
        is_email = request.data.get("is_email", False)
        user_status = request.data.get("status", None)

        if user_status:
            users = CustomUser.objects.filter(status=user_status).delete()

        if is_email:
            users = CustomUser.objects.filter(email=email_or_phone).delete()
        else:
            users = CustomUser.objects.filter(contact_number=email_or_phone).delete()

        return Response(
            {"users": users, "message": messages.SUCCESS}, status=status.HTTP_200_OK
        )


class ImageUploadView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (OAuth2Authentication, JWTAuthentication)

    def post(self, request, *args, **kwargs):
        image = request.FILES.get("image")
        bucket = config("S3_BUCKET_NAME")
        key = request.data.get("key")

        if image:
            # Upload the image to S3 using boto3
            s3 = boto3.client(
                "s3",
                aws_access_key_id=config("s3AccessKey"),
                aws_secret_access_key=config("s3Secret"),
            )
            key = f"{image.name}"  # Change the key as needed
            s3.upload_fileobj(image, bucket, key, ExtraArgs={"ACL": "public-read"})

            # Generate the URL for the uploaded image
            url = f"https://{bucket}.s3.amazonaws.com/{key}"

            return Response({"url": url}, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST
            )


class AllPromotionalMessageView(ListAPIView):
    serializer_class = PromotionalMesssageSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    pagination_class = CustomPagination
    queryset = PromotionalMesssage.objects.all().order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RetrievePromotionalMessageView(RetrieveAPIView):
    serializer_class = PromotionalMesssageSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    queryset = PromotionalMesssage.objects.all()
    lookup_field = "id"

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super(RetrievePromotionalMessageView, self).__init__(**kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format)


class CreatePromotionalMessageView(CreateAPIView):
    serializer_class = PromotionalMesssageSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        all_users = CustomUser.objects.all()
        user_type = request.data["userType"]
        if user_type:
            customers = all_users.filter(status="ACTIVE", role=user_type).values_list(
                "id", flat=True
            )
            instance = serializer.instance
            message = request.data["description"]
            params = "{" + '"promotion_id": {}'.format(instance.id) + "}"
            for user in customers:
                notification_data = {
                    "message": message,
                    "status": "UR",
                    "user_id": user,
                    "notification_type": "NEW_PROMOTION",
                    "params": params,
                }
                req = NotificationSerializer(data=notification_data)
                if req.is_valid(raise_exception=True):
                    req.save()
                    UserLoginAPIView.generate_fcm_token(
                        self,
                        user,
                        notification_data,
                        True if user_type == "USER" else False,
                    )
        if not scheduler.running:
            start_scheduler()
            scheduler.add_job(
                send_promotional_mail_to_users, "date", run_date=datetime.now()
            )
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_201_CREATED
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_201_CREATED)


class DestroyPromotionalMessageView(DestroyAPIView):
    serializer_class = PromotionalMesssageSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    queryset = PromotionalMesssage.objects.all()
    lookup_field = "id"

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.response_format["data"] = None
        self.response_format["status_code"] = status.HTTP_204_NO_CONTENT
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_204_NO_CONTENT)


class UpdatePromotionalMessageView(UpdateAPIView):
    serializer_class = PromotionalMesssageSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, IsTokenValid, IsSuperAdmin)
    queryset = PromotionalMesssage.objects.all()
    lookup_field = "id"

    def __init__(self, **kwargs):
        """
        Constructor function for formatting the web response to return.
        """
        self.response_format = ResponseInfo().response
        super().__init__(**kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Handle PATCH requests for updating an existing PromotionalMessage instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        self.response_format["data"] = serializer.data
        self.response_format["status_code"] = status.HTTP_200_OK
        self.response_format["error"] = None
        self.response_format["message"] = messages.SUCCESS
        return Response(self.response_format, status=status.HTTP_200_OK)

class GetDownloadCount(APIView):
    """
    API endpoint to return a static number of installs/downloads.
    """

    def get(self, request):
        return Response({"downloads": "1M+"}, status=status.HTTP_200_OK)        
