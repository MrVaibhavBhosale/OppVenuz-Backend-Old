"""
This file is used as common utility functionality.
"""
import random
import string

import urllib.request
import urllib.parse
from rest_framework.views import exception_handler
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework import status
from users.models import City
from utilities import constants

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Update the structure of the response data.
    if response is not None:
        customized_response = dict()
        customized_response['error'] = []

        for key, value in response.data.items():
            error = key
            customized_response['status_code'] = response.status_code
            customized_response['error'] = error
            customized_response['data'] = None
            customized_response['message'] = value

        response.data = customized_response

    return response


def send_sms(apikey, numbers, sender, message):
    data = urllib.parse.urlencode({'apikey': apikey, 'numbers': numbers,
                                   'message': message, 'sender': sender})
    data = data.encode('utf-8')
    request = urllib.request.Request("https://api.textlocal.in/send/?")
    f = urllib.request.urlopen(request, data)
    fr = f.read()
    return fr


class ResponseInfo(object):

    def __init__(self, user=None, **args):
        self.response = {
            "status_code": args.get('status', 200),
            "error": args.get('error', None),
            "data": args.get('data', []),
            "message": args.get('message', 'Success')
        }


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data, bookmark=None):
        return Response({
            "status_code": status.HTTP_200_OK,
            "error": None,
            "data": {
                'links': {
                    'total_pages': self.page.paginator.num_pages,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                    'bookmark': bookmark,
                },
                'count': self.page.paginator.count,
                'results': data
            },
            "message": "Success"
        })


def generate_password():
    special_chars = constants.SPECIAL_CHARS
    chars = string.ascii_letters + string.digits

    # Define the password length range
    min_length = 8
    max_length = 14

    # Ensure the password length is within the specified range
    password_length = random.randint(min_length, max_length)

    # Ensure the password contains at least one special character & one digit
    password = random.choice(special_chars)
    password += random.choice(string.ascii_uppercase)
    password += random.choice(string.digits)

    # Add random alphabets and numbers to the password
    for _ in range(password_length - 3):
        password += random.choice(chars)

    # Shuffle the characters in the password
    password_list = list(password)
    random.shuffle(password_list)
    password = ''.join(password_list)

    return password


def get_otp():
    """generate otp

    Args:
        length (int, optional): length of the otp. Defaults to constants.OTP_LENGTH.
    """
    return random.randint(1000, 9999)


def is_existing_user(user):
    '''
    return true if user is already existing
    '''
    if user.fullname and user.state and user.city:
        return True
    return False


def set_user_city_state(user):
    if user.address:
        city = City.objects.filter(city_name=user.address, state__state_name=user.address_state)
        if city.exists():
            city = city.first()
            user.city = city
            user.state = city.state
            user.save()