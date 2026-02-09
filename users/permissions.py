from rest_framework.permissions import BasePermission
from .models import BlackListedToken
from plan.models import VendorPlan


class IsAdminOrIsSelf(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Super admin check
        if request.user.is_superuser:
            return True
        # Check if the logged-in user is accessing their own details
        return obj == request.user

class IsTokenValid(BasePermission):
    """
    Class for validating if the token is present in the blacklisted token list.
    """

    def has_permission(self, request, view):
        """
        Function for checking if the caller of this function has
         permission to access particular API.
        """
        is_allowed_user = True
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            key, token = auth_header.split(' ')
            if key == 'Bearer':
                try:
                    is_blacklisted = BlackListedToken.objects.get(token=token)
                    if is_blacklisted:
                        is_allowed_user = False
                except BlackListedToken.DoesNotExist:
                    is_allowed_user = True
                return is_allowed_user
        else:
            is_allowed_user = False
            return is_allowed_user


class IsPlatinumUser(BasePermission):
    def has_permission(self, request, view):
        is_platinum_user = False
        vendor_plan = VendorPlan.objects.filter(vendor_service_id=request.data["vendor_service_id"]).order_by("-created_on").first()
        # vendor_plan = VendorPlan.objects.filter(vendor_service_id=request.data["vendor_service_id"]).values(
        #     "plan_id_id__subscription_type")
        if vendor_plan:
            subscription_type = vendor_plan.subscription_type
            if subscription_type == "PLATINUM":
                is_platinum_user = True
        return is_platinum_user


class IsSuperAdmin(BasePermission):
    '''
    Check if a user is superadmin
    '''
    def has_permission(self, request, view):
        return request.user.role == 'SUPER_ADMIN'
            