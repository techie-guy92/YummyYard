from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignUpAPIView, ResendVerificationEmailAPIView, VerifyEmailAPIView, LoginAPIView,UserProfileAPIView, 
    UpdateUserAPIView, FetchUsersModelViewSet, PasswordResetAPIView, SetNewPasswordAPIView,
)

router = DefaultRouter()
router.register(r"fetch-users", FetchUsersModelViewSet, basename="fetch-users")


urlpatterns = [
    path("sign-up/", SignUpAPIView.as_view(), name="sign-up"),
    path("resend-verification-email/", ResendVerificationEmailAPIView.as_view(), name="resend-verification-email"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("user-profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("update-user/", UpdateUserAPIView.as_view(), name="update-user"),
    path("password-reset/", PasswordResetAPIView.as_view(), name="password-reset"),
    path("set-new-password/", SetNewPasswordAPIView.as_view(), name="set-new-password"),
]


urlpatterns += router.urls