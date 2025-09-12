from django.core.exceptions import PermissionDenied


def user_is_manager(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if user.role == 'Manager':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrap


def user_is_hr(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if user.role == 'HR':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrap


def user_is_employee(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        if user.role == 'Employee':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrap