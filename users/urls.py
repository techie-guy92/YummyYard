from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignUpAPIView, VerifyEmailAPIView, LoginAPIView, UserProfileAPIView, 
    PartialUserUpdateAPIView, FetchUsersModelViewSet, PasswordResetAPIView, SetNewPasswordAPIView,
    BucketFilesView, BucketResultView, FileDeleteView, BulkDeleteView, FileDeleteResultView, 
    FileDownloadView, FileDownloadResultView, RequestEmailChangeAPIView, 
)

router = DefaultRouter()
router.register(r"fetch-users", FetchUsersModelViewSet, basename="fetch-users")


urlpatterns = [
    path("sign-up/", SignUpAPIView.as_view(), name="sign-up"),
    # path("resend-verification-email/", ResendVerificationEmailAPIView.as_view(), name="resend-verification-email"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify-email"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("user-profile/", UserProfileAPIView.as_view(), name="user-profile"),
    path("update-user/", PartialUserUpdateAPIView.as_view(), name="update-user"),
    path("password-reset/", PasswordResetAPIView.as_view(), name="password-reset"),
    path("set-new-password/", SetNewPasswordAPIView.as_view(), name="set-new-password"),
    path("update-email/", RequestEmailChangeAPIView.as_view(), name="update-email"),
    # ArvanCloud
    path("admin/bucket/files/", BucketFilesView.as_view(), name="bucket-files"),
    path("admin/bucket/result/<str:task_id>/", BucketResultView.as_view(), name="bucket-files-result"),
    path("admin/bucket/delete/", FileDeleteView.as_view(), name="file-delete"),
    path("admin/bucket/delete/bulk/", BulkDeleteView.as_view(), name="bulk-delete"),
    path("admin/bucket/delete/result/<str:task_id>/", FileDeleteResultView.as_view(), name="file-delete-result"),
    path("admin/bucket/download/", FileDownloadView.as_view(), name="file-download"),
    path("admin/bucket/download/<str:task_id>/", FileDownloadResultView.as_view(), name="file-download-result"),
]   

urlpatterns += router.urls