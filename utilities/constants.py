import os

from decouple import config

# load_dotenv()

FORGOT_PASSWORD_URL = config("FORGOT_PASSWORD_URL", "")
VENDOR_FORGOT_PASSWORD_URL = config("VENDOR_FORGOT_PASSWORD_URL", "")
USER_FORGOT_PASSWORD_URL = config("USER_FORGOT_PASSWORD_URL", "")

FCM_BASE_URL = "https://fcm.googleapis.com"
DELETED = "DELETED"
UNPAID = "UNPAID"
SUPER_ADMIN = "SUPER_ADMIN"
VENDOR = "VENDOR"
SPECIAL_CHARS = "!@#$%&*"
ADMIN_VENDOR_REGISTRATION_TEMPLATE = "d-1297f124c34b41239e614d48e54282c3"
VENDOR_WELCOME_TEMPLATE = "d-7b5f28e639614416a506dcca49ad2020"
WELCOME_TEMPLATE = "d-f31d699a4f884c4ea595b99e27a54bf3"
VENDOR_APPROVAL_TEMPLATE = "d-fbd03941a84d4c25b78f5ea132f05f64"
VENDOR_PAYMENT_DONE_TEMPLATE = "d-018696850344465c8c0757b836f195ff"
VENDOR_PAYMENT_PENDING_TEMPLATE = "d-f57edbfb776b480cba7d00b59f956963"
USER_ENQUIRY_TEMPLATE = "d-0e19392e73a447a4912f715db6288c73"
CELEBRITY_ENQUIRY_TEMPLATE = "d-f347276b53c94bf78f26b523ea0e31a7"
VENDOR_ADDED_TO_CART_TEMPLATE = "d-29b21a5af7d84f8fab79a77f0dc40273"
# VENDOR_ADDED_TO_CART_TEMPLATE = "d-5f55c93ce7b84961a3e1dc049dab55bb"
USER_ADS_SERVICE_TO_CART = "d-d06079aa923448519638b9d33fbeb262"
VENDOR_FILLED_CONTACT_US_TEMPLATE = "d-849e7ad9a50141e789e66919851b91a5"
FORGOT_PASSWORD_TEMPLATE = "d-b5d9a417cb5a45b590610ed98733a019"
VENDOR_INVITATION_TEMPLATE = "d-3b7ec5e566a24b8c930d26a23c72c7b3"
VENDOR_EMAIL_VERIFICATION_TEMPLATE = "d-313fc9cdbe7c4610a158e4786ac45b59"
USER_REGISTER_TEMPLATE = "d-43374f3e025546e28b8ac4ef155fd423"
NEW_PROMO_FOR_ADMIN_TEMPLATE = "d-61af2af038bf4d21a1f393f7883bc0c1"
NEW_PROMO_FOR_VENDOR_TEMPLATE = "d-30db60d735cf4388abff1f7336ff47c8"
NEW_PROMO_FOR_USER_TEMPLATE = "d-37209f1f078f4b8ebee9379695272ca6"

PHONE_VERIFICATION_MSG_TEMPLATE = (
    "{} is OTP for verifying your phone number as a Vendor on OppVenuz."
)
USER_PHONE_VERIF_TEMPLATE = (
    "{} OTP for verifying your phone number as a User on OppVenuz."
)
PINTEREST_API_URL = "https://api.pinterest.com/v5/pins"
USER_SEND_SERVICE_ENQUIRY_TEMPLATE = "d-0bb7633072e54cf8a398605b437d737f"
# BRANCHIO_REDIRECT_PATH="/home/cart/shared-cart-detail"
BRANCHIO_REDIRECT_PATH_STAGE = "https://stage-nextjs.oppvenuz.com/event-budget/"
BRANCHIO_REDIRECT_PATH_DEV = "https://dev-nextjs.oppvenuz.com/event-budget/"
BRANCHIO_REDIRECT_PATH = "https://www.oppvenuz.com/event-budget/"


BRANCHIO_SERVICE_SHARE_PATH_STAGE = (
    "https://stage-nextjs.oppvenuz.com/vendors/?service={}&id={}"
)
BRANCHIO_SERVICE_SHARE_PATH_DEV = (
    "https://dev-nextjs.oppvenuz.com/vendors/?service={}&id={}"
)
BRANCHIO_SERVICE_SHARE_PATH = "https://www.oppvenuz.com/vendors/?service={}&id={}"


CLIENT_NUMBER = "7720956565"
# CLIENT_EMAIL = "kiranmokashi0502@gmail.com"
CLIENT_EMAIL = "support@oppvenuz.com"
TEST_EMAIL = "rajat.jog@mindbowser.com"
PLATINUM = "PLATINUM"
EVENT = "Service Event"
SCHEDULER_STARTED = "Scheduler started successfully"
SCHEDULER_STOPPED = "Scheduler shut down successfully!"
# ADHAR_OTP_REQUEST_URL = "https://in-aadhaarxml-verify.staging-signdesk.com/api/requestOTP"
ADHAR_OTP_REQUEST_URL = "https://in-aadhaarxml-verify.signdesk.com/api/requestOTP"
ADHAR_OTP_VERIFY_URL = "https://in-aadhaarxml-verify.signdesk.com/api/submitOTP"
PAN_VERIFY_URL = "https://in-pan-verify.signdesk.com/api/panVerification"
GST_VERIFY_URL = "https://in-gst-verify.signdesk.com/api/gstVerification"
MSME_VERIFY_URL = "https://in-uan-verify.signdesk.com/api/udhyogAadhaarNumberV2"
BRANCH_CART_URL = "https://api2.branch.io/v1/url"
GOOGLE_KEY_FILE = (
    "./oppvenuz/google_play_console/pc-api-8818528044491383164-562-2a011162716c.json"
)
# https://oppvenuz-dev-uploads.s3.amazonaws.com/play_console.json
LISTED_CITIES = [
    "Kochi",
    "Kanpur",
    "Varanasi",
    "Visakhapatnam",
    "Coimbatore",
    "Bhopal",
    "Lucknow",
    "Agra",
    "Indore",
    "Ahmadabad",
    "Surat",
    "Jaipur",
    "Chandigarh",
    "goa",
    "Kolkata",
    "Hyderabad",
    "Delhi NCR",
    "Chennai",
    "Bangalore",
    "Nagpur",
    "Mumbai",
    "Pune",
]

USER_ADD_SERVICE_CART = """
Great choice! Your item has been added to the cart. Happy event!

OppVenuz
"""
ADMIN_REC_WHEN_VENDOR_REG_BY_ADMIN = "d-4c440b888e97446eb31690fed556a71b"
ADMIN_REC_ON_CELEB_ENQ_BY_USER = "d-ca13f941fccc4601a29e383d4640e774"
