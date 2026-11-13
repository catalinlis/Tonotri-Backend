from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    Requires an active account and email confirmation for regular users.
    """

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (not user.regular_user or user.confirmed_email)
        )
