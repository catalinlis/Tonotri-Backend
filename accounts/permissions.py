from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    Allows access only to authenticated AND active users.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.regular_user:
            return (
                user 
                and user.is_authenticated
                and user.is_active
                and user.confirmed_email
            )

        return (
            user
            and user.is_authenticated
            and user.is_active
        )