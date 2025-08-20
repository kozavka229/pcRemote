from rest_framework.exceptions import APIException

class Http401(APIException):
    status_code = 401
    default_detail = "Not logged in"
