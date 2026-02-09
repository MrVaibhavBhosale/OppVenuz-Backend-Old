import pandas as pd
from service.models import Service, VendorService
from plan.models import Plan, VendorPlan

def create_plans():
    filename = 'plan__plan.csv'
    df = pd.read_csv(filename)

    vendor_plans = []
    dl = Plan.objects.all().delete()
    vpn = VendorPlan.objects.all().delete()

    for _, row in df.iterrows():
        row_dict = row.to_dict()

        try:
            service = Service.objects.get(slug=row_dict['service_slug'])
            # print(service, service.id)
            row_dict['service_id_id'] = service.id

            del row_dict['service_slug']
            
            plan = Plan.objects.create(**row_dict)

            if row_dict['validity_type'] == 'Free':
                vendor_services = VendorService.objects.filter(service_id=service, approval_status='A')
                for vendor_service in vendor_services:
                    vp = VendorPlan(
                        vendor_service_id=vendor_service,
                        plan_id=plan,
                        starts_from="2024-06-27T16:15:53.058Z",
                        ends_on="2122-06-27T16:15:53.058Z",
                        plan_status="ACTIVE",
                        duration_in_months=0,
                        subscription_type="SILVER",
                    )
                    vendor_plans.append(vp)
        except Service.DoesNotExist:
            print(f"Service with slug '{row_dict['service_slug']}' does not exist.")
        except Exception as e:
            print(f"Validation error for row {row_dict}: {e}")
    VendorPlan.objects.bulk_create(vendor_plans)