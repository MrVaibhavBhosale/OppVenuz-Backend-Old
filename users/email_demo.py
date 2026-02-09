import sendgrid
import os
from sendgrid.helpers.mail import Email, Substitution, Mail, Personalization
from python_http_client import exceptions
from decouple import config
# load_dotenv()


sg = sendgrid.SendGridAPIClient(config("SENDGRID_API_KEY"))
mail = Mail()
mail.template_id = "d-1772e8ac6b5442e68975394ea71a4957"

mail.from_email = Email("shubham.yadav@mindbowser.com")
personalization = Personalization()
personalization.add_to(Email("shubhamyadav0503@gmail.com"))
mail.subject = "I'm replacing the subject tag"
personalization.dynamic_template_data = {"user_name": "Shubham"}
mail.add_personalization(personalization)
# personalization.add_dynamic_template_data(Substitution("-reset_token$-", "https://mail.google.com/mail/u/0/#inbox"))
try:
    response = sg.client.mail.send.post(request_body=mail.get())
except exceptions.BadRequestsError as e:
    print(e.body)
    exit()
