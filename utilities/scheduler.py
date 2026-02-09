"""
Apscheduler
"""

import logging
import os
from datetime import datetime
from decouple import config
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from e_invites.models import Template
from utilities import constants
from django.db.models import Q
from users.models import CustomUser
from utilities.commonutils import send_email

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_jobstore(DjangoJobStore(), "default")


def update_placid_templates():
    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {config('EINVITE_BEARER_TOKEN')}",
    }
    url = "https://api.placid.app/api/rest/templates"
    uids = set()
    while url:
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        templates = data.get("data")
        for template in templates:
            uid = template.pop("uuid")
            uids.add(uid)
            print(len(uids))
            temp = Template.objects.filter(Q(uuid=uid) | Q(uid=uid)).update_or_create(
                uid=uid, defaults=dict(template), is_active=True
            )
        url = data.get("links", {}).get("next")
    deleted_templates = Template.objects.exclude(Q(uuid__in=uids) | Q(uid__in=uids))
    deleted_templates.delete()
    # print(deleted_templates, len(deleted_templates))


def start_scheduler():
    """
    Start the scheduler
    """
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info(constants.SCHEDULER_STARTED)
        scheduler.add_job(
            update_placid_templates,
            "interval",
            hours=4,
            id="update_placid_templates",  # The `id` assigned to each job MUST be unique
            max_instances=2,
            replace_existing=True,
            misfire_grace_time=None,
            next_run_time=datetime.now(),
        )
        print("update_placid_templates job added !!")
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info(constants.SCHEDULER_STOPPED)


def send_promotional_mail_to_users():
    users = CustomUser.objects.filter(status="ACTIVE").exclude(
        email=constants.CLIENT_EMAIL
    )
    for user in users:
        if user.role == "VENDOR" and user.email:
            template_id = constants.NEW_PROMO_FOR_VENDOR_TEMPLATE
            data = {"user": user.fullname.title()}
            send_email(template_id, user.email, data)
            print("sent to vendor", user.email)

        if user.role == "USER" and user.email:
            template_id = constants.NEW_PROMO_FOR_USER_TEMPLATE
            data = {"user": user.fullname.title()}
            send_email(template_id, user.email, data)
            print("sent to user", user.email)

        if user.role == "SUPER_ADMIN" and user.email:
            template_id = constants.NEW_PROMO_FOR_ADMIN_TEMPLATE
            data = {"user": user.fullname.title()}
            send_email(template_id, user.email, data, bcc=True)
            print("sent to admin", user.email)
