from django.contrib import admin

# Register your models here.
"""
This is admin file for project app of the mypm project,
 used for registering the users app with the mypm project.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from users.models import CustomUser, InviteUser, City, Notification, PhoneVerification, State

admin.site.unregister(Group)
# admin.site.register(CustomUser)
admin.site.register(InviteUser)
admin.site.register(City)
admin.site.register(State)
admin.site.register(Notification)
admin.site.register(PhoneVerification)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'id', 'email', 'fullname', 'contact_number', 'status', 'role',
    ]
    list_display_links = ['id', 'email', 'fullname', 'contact_number']
    list_filter = ['status', 'role', 'payment_status']
    ordering = ['-id', 'email', 'fullname', 'contact_number']
    search_fields = ['email', 'fullname', 'contact_number', 'id']