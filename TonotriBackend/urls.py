"""
URL configuration for TonotriBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import CustomRegisterView, CustomLoginView, RegisterStep
from accounts.views import GoogleLogin, CustomLogoutView, ProfileView, CheckTokenView
from accounts.views import GenerateValidationToken, ValidateToken, NextStep
from explore.views import LocationPhotos, CountryDescriptionAI, CountryCities, CityDescriptionAI

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Explicitly defining the paths to avoid 404s
    path('api/auth/register/', CustomRegisterView.as_view(), name='register'),
    path('api/auth/login/', CustomLoginView.as_view(), name='login'),
    path('api/auth/logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Explicit Social Login Route
    # This forces the /google/ endpoint to exist
    path('api/auth/social/google/', GoogleLogin.as_view(), kwargs={'provider': 'google'}, name='google_login'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/token/check/', CheckTokenView.as_view(), name='check_token'),
    path('api/token/generation/', GenerateValidationToken.as_view(), name='generate_token'),
    path('api/token/validation/', ValidateToken.as_view(), name='validate_token'),
    path('api/registration/step/', RegisterStep.as_view(), name='register_step'),
    path('api/registration/next/', NextStep.as_view(), name='register_next_step'),
    path('api/media/', include('media.urls')),
    path('api/users/', include('users.urls')),
    path('api/explore/location-photos/', LocationPhotos.as_view(), name='location_photos'),
    path('api/explore/country-description/', CountryDescriptionAI.as_view(), name='country_description'),
    path('api/explore/country-cities/', CountryCities.as_view(), name='country_cities'),
    path('api/explore/city-description/', CityDescriptionAI.as_view(), name='big_city_description'),
]
