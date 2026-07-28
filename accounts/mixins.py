class AuthCookieMixin:
    """
    Mixin for setting JWT tokens in HttpOnly cookies after login 
    or social login and removing them from the response body.
    """

    def set_auth_cookies(self, response, access_token=None, refresh_token=None):
        """
        Sets access and refresh tokens in HttpOnly cookies
        and a visible loggedIn cookie.
        Removes 'access' and 'refresh' tokens from body data
        Concerning access_token and refresh_token, the tokens
        are created at every Login, Register, Social auth
        """

        if(access_token):
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=3600
            )

        if(refresh_token):
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7*24*3600
            )

        response.set_cookie(
            key='loggedIn',
            value='true',
            httponly=False,
            secure=False,
            samesite='Lax',
            max_age=7*24*3600
        )

        # response.data.pop('access', None)
        # response.data.pop('refresh', None)
        # print(response)

        return response

    def delete_auth_cookies(self, response):
        """
        Delete JWT cookies for logout
        """
        response.delete_cookie('auth-jwt', path='/', samesite='Lax')
        response.delete_cookie('auth-refresh-jwt', path='/', samesite='Lax')
        response.delete_cookie('loggedIn', path='/', samesite='Lax')

        return response