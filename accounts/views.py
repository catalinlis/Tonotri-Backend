from auth_kit.social.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from auth_kit.views import RegisterView, LoginView, LogoutView
from .serializers import CustomRegisterSerializer, UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsActiveUser
from rest_framework import status
from .mixins import AuthCookieMixin
from .tasks import send_email_task
from users.models import User
from accounts.utils.redis_utils import VerificationEmail
import uuid
import secrets
import sys

VerificationEmail = VerificationEmail()

class GoogleLogin(AuthCookieMixin, SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "postmessage"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        return self.set_auth_cookies(response)

class CustomRegisterView(AuthCookieMixin, RegisterView):
    serializer_class = CustomRegisterSerializer

    def get_response_data(self, user):
      # Override to include guid in the registration response
      response = super().get_response_data(user)
      response['guid'] = str(user.guid)

      response.pop('access', None)
      response.pop('refresh', None)
      response.pop('user', None)

      return response

class CustomLoginView(AuthCookieMixin, LoginView):

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return self.set_auth_cookies(response)

class CustomLogoutView(AuthCookieMixin, LogoutView):
    permission_classes = [IsAuthenticated]

    def logout(self, request):
        response = super().logout(request)

        return self.delete_auth_cookies(response)

class ProfileView(APIView):
  permission_classes = [IsActiveUser]

  def get(self, request):

    serializer = UserProfileSerializer(request.user)

    return Response(serializer.data)

class CheckTokenView(APIView):
  permission_classes = [AllowAny]
  authentication_classes = []

  def get(self, request):
    token = request.query_params.get('guid')

    if not token:
      return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
      guid = uuid.UUID(token)
    except ValueError:
      return Response({'error': 'Invalid token format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
      user = User.objects.get(guid=guid)
    except User.DoesNotExist:
      return Response({'error': 'The token does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

    if user.regular_user and not user.confirmed_email:
      return Response(status=status.HTTP_200_OK)
    
    return Response({'error': 'The token does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

class GenerateValidationToken(APIView):
  permission_classes = [AllowAny]
  authentication_classes = []

  def post(self, request):
    guid = request.data.get('guid')
    
    if not guid:
      return Response(
        {'error': 'GUID is required'},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    user = User.objects.filter(guid__exact=guid).first()
    
    if not user:
      return Response(
        {'error': 'User not found'},
        status=status.HTTP_400_BAD_REQUEST
      )

    if not user.email:
      return Response(
        {'error': 'User does not have email'},
        status=status.HTTP_400_BAD_REQUEST
      )

    if user.confirmed_email:
      return Response(
        {'error': 'User is already active'},
        status=status.HTTP_400_BAD_REQUEST
      ) 

    # Generate 6-digit token
    token = str(secrets.randbelow(900000) + 100000)

    try:
      feedback = VerificationEmail.set_code(user.email, token)
      if feedback != "OK":
        return Response(
          {'error': feedback},
          status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
      return Response(
        {'error': str(e)},
        status=429
      )

    # Send email asycnhronously
    send_email_task.delay(
      subject = "Account activation",
      message = f"Hello from Tonotri,\n\nYour confirmation code is {token}, it will expire in 60 seconds.",
      recipient_list = [user.email]
    )
     
    return Response({
      'status': 'success',
      'message': f'Confirmation code sent to {user.email}'
      },
      status=status.HTTP_200_OK
    )

class ValidateToken(APIView):
  permission_classes = [AllowAny]
  authentication_classes = []

  def post(self, request):
    guid = request.data.get('guid')
    token = request.data.get('code')
    
    if not guid:
      return Response(
        {'error': 'GUID is required'},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    user = User.objects.filter(guid__exact=guid).first()
    
    if not user:
      return Response(
        {'error': 'User not found'},
        status=status.HTTP_400_BAD_REQUEST
      )

    if not user.email:
      return Response(
        {'error': 'User does not have email'},
        status=status.HTTP_400_BAD_REQUEST
      )

    if user.confirmed_email:
      return Response(
        {'error': 'User is already active'},
        status=status.HTTP_400_BAD_REQUEST
      ) 

    try:
      isValid = VerificationEmail.compare_code(user.email, token)
      if isValid:
        user.confirmed_email = True
        user.save()
        
        return Response(
          {'status': 'success'},
          status=status.HTTP_200_OK
        )

      else:
        return Response(
          {'error': 'The confirmation code is not valid.'},
          status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
      return Response(
        {'error': str(e)},
        status=429
      )

class RegisterStep(APIView):
  permission_classes = [IsActiveUser]

  def get(self, request):
    user = request.user

    return Response({'step': f'{user.register_step}'}, status=status.HTTP_200_OK)

class NextStep(APIView):
  permission_classes = [IsActiveUser]

  def post(self, request):
    user = request.user

    if user.register_step == User.RegistrationStep.ADD_PHOTO:
      user.register_step = User.RegistrationStep.VISITED_COUNTRIES
    elif user.register_step == User.RegistrationStep.VISITED_COUNTRIES:
      user.register_step = User.RegistrationStep.DONE

    user.save()

    return Response(status=status.HTTP_200_OK)

