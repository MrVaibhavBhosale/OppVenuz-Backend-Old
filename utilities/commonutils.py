import os
import json

import requests
import sendgrid
from sendgrid.helpers.mail import Mail, Email, Personalization, Bcc
from python_http_client import exceptions
from oppvenuz.settings.settings import (
    DEFAULT_FROM_EMAIL,
    VENDOR_FROM_EMAIL,
    GOOGLE_SERVICE_ACCOUNT_KEY_FILE,
)
from inapppy import GooglePlayVerifier
from decouple import config
from inapppy import AppStoreValidator
from inapppy import InAppPyValidationError
from users.models import CustomUser
from utilities.constants import DELETED, UNPAID
from .constants import CLIENT_EMAIL

# load_dotenv()
GOOGLE_SERVICE_ACCOUNT_KEY_FILE = GOOGLE_SERVICE_ACCOUNT_KEY_FILE


def send_email(template_id, recipient, data_dict, bcc=False):
    """
    Function to connect with sendgrid and send emails to receivers
    """
    sender = DEFAULT_FROM_EMAIL
    sg = sendgrid.SendGridAPIClient(config("SENDGRID_API_KEY"))
    mail = Mail()
    mail.template_id = template_id

    mail.from_email = Email(sender)
    personalization = Personalization()
    personalization.add_to(Email(recipient))
    personalization.dynamic_template_data = data_dict
    mail.add_personalization(personalization)
    if bcc:
        # mail.add_bcc(Bcc(VENDOR_FROM_EMAIL))

        mail.add_bcc(Bcc(CLIENT_EMAIL))
    try:
        if recipient:
            response = sg.client.mail.send.post(request_body=mail.get())
    except exceptions.BadRequestsError as e:
        print(e.body)
        exit()
    print(response.status_code)
    return None


def google_validator(purchase_token, product_sku):
    """
    Accepts receipt, validates in Google.
    """
    GOOGLE_BUNDLE_ID = config("GOOGLE_BUNDLE_ID", None)
    purchase_token = purchase_token
    product_sku = product_sku
    verifier = GooglePlayVerifier(
        GOOGLE_BUNDLE_ID,
        GOOGLE_SERVICE_ACCOUNT_KEY_FILE,
    )
    response = {"valid": False, "transactions": []}

    result = verifier.verify_with_result(
        purchase_token, product_sku, is_subscription=True
    )

    # result contains data
    raw_response = result.raw_response
    is_canceled = result.is_canceled
    is_expired = result.is_expired

    return result


def verify_google_play(purchase_token, product_sku):
    """
    google play console validation
    """
    # GOOGLE_BUNDLE_ID = "com.oppvenuzvendor"
    GOOGLE_BUNDLE_ID = config("GOOGLE_BUNDLE_ID", None)
    # GOOGLE_FILE_PATH = str(BASE_DIR) + GOOGLE_SERVICE_ACCOUNT_KEY_FILE
    GOOGLE_FILE_PATH = GOOGLE_SERVICE_ACCOUNT_KEY_FILE

    verifier = GooglePlayVerifier(
        GOOGLE_BUNDLE_ID,
        GOOGLE_FILE_PATH,
    )
    result = verifier.verify_with_result(
        purchase_token, product_sku, is_subscription=True
    )
    raw_response = result.raw_response
    is_canceled = result.is_canceled
    is_expired = result.is_expired

    return result


def check_expiration_intent(data, subscription_id):
    if data["auto_renew_product_id"] == subscription_id:
        if "expiration_intent" in data:
            if data["expiration_intent"] == "1":
                return True
    return False


def verify_apple_receipt(receipt, subscription_id):
    """
    apple in purchase receipt validation
    """
    bundle_id = config("GOOGLE_BUNDLE_ID", None)
    optional_shared_secret = config("OPTIONAL_SHARED_SECRET", None)
    auto_retry_wrong_env_request = config(
        "SAND_BOX", False
    )  # if True, automatically query sandbox endpoint if
    # validation fails on production endpoint
    validator = AppStoreValidator(
        bundle_id, auto_retry_wrong_env_request=auto_retry_wrong_env_request
    )

    try:
        exclude_old_transactions = (
            False  # if True, include only the latest renewal transaction
        )
        validation_result = validator.validate(
            receipt,
            optional_shared_secret,
            exclude_old_transactions=exclude_old_transactions,
        )
    except InAppPyValidationError as ex:
        validation_result = None
        response_from_apple = (
            ex.raw_response
        )  # contains actual response from AppStore service.
    data = {}
    if validation_result:
        if "pending_renewal_info" in validation_result:
            pending_renewal_info_data = validation_result["pending_renewal_info"]
            product_expire = [
                True
                for data in pending_renewal_info_data
                if check_expiration_intent(data, subscription_id)
            ]
            if len(product_expire) > 0:
                if product_expire[0]:
                    data.update({"is_expire": True, "status": True})
            else:
                if validation_result["status"] == 0:
                    data.update({"is_expire": False, "status": True})
        else:
            if validation_result["status"] == 0:
                data.update({"is_expire": False, "status": True})
    else:
        data.update({"is_expire": True, "status": False})
    return data


def user_delete(email):
    """
    if user delete his own account that time status is changed if same email through again signup apply that time old
    user data delete.
    """
    users = CustomUser.objects.filter(email=email, status=DELETED)
    users.delete()
    return None


def vendor_plan_status_update(vendor_plan_data):
    vendor_service = vendor_plan_data.vendor_service_id
    vendor_service.payment_status = UNPAID
    vendor_service.save()
    return None


def deleted_vendor_service_remove(user_data):
    """
    vendor user delete time vendor service also delete
    """
    user_data.vendorservice_set.all().delete()
    return None
