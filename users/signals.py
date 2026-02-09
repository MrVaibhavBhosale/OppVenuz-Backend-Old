from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import AdminRolesMaster

@receiver(post_migrate)
def create_admin_roles(sender, **kwargs):
    """
    Function to check and insert admin roles after migration with specific IDs.
    """
    roles = [
        (1, 'VS view', 'View all the vendors'), 
        (2, 'VS add', 'Add new vendor'), 
        (3, 'VS edit', 'Edit vendor details'), 
        (4, 'VS delete', 'Delete vendor'), 
        (5, 'VS suspend', 'Suspend vendor'),
        (6, 'AR view', 'View Articles'), 
        (7, 'AR add', 'Add Articles'),
        (8, 'AR edit', 'Edit Articles'),
        (9, 'AR delete', 'Delete Articles'),
        (10, 'CB view', 'View Celebrities'),
        (11, 'CB add', 'Add Celebrities'),
        (12, 'CB edit', 'Edit Celebrities'),
        (13, 'CB delete', 'Delete Celebrities'),
        (14, 'CB open', 'Open Celebrity Enquiry'),
        (15, 'CB close', 'Close Celebrity Enquiry'),
        (16, 'Add City', 'Add city tav'),
        (17, 'Reports', 'Reports Tab'),
        (18, 'BE view', 'Bussiness Enquiry view'),
        (19, 'BE approve', 'Bussiness Enquiry approve'),
        (20, 'BE reject', 'Bussiness Enquiry reject'),
        (21, 'SUB view', 'Subscription view'),
        (22, 'SUB wave off fee', 'Subscription wave off fee'),
    ]

    # AdminRolesMaster.objects.all().delete()

    # for role_id, role_name, role_desc in roles:
    #     AdminRolesMaster.objects.create(id=role_id, role_name=role_name, role_desc=role_desc)

    for role_id, role_name, role_desc in roles:
        role, created = AdminRolesMaster.objects.update_or_create(
            id=role_id,
            defaults={'role_name': role_name, 'role_desc': role_desc}
        )
