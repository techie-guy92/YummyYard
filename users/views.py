from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.http import FileResponse, HttpResponse
from celery.result import AsyncResult
from logging import getLogger
from django.urls import reverse
from urllib.parse import urlencode
from django.utils import timezone
import os
import json
import uuid
from .models import *
from .serializers import *
from .tasks import fetch_all_files, remove_file, download_obj
from utilities import email_sender
from custom_permission import CheckOwnershipPermission
from custome_throttling import CustomThrottle
from custome_exception import CustomEmailException, CustomRedisException


#======================================== Utilities ==============================================

class EmailChangeThrottle(CustomThrottle):
    def __init__(self):
        super().__init__(scope="email_change", seconds=1800)


class PasswordResetThrottle(CustomThrottle):
    def __init__(self):
        super().__init__(scope="password_reset", seconds=86400)
        
        
# ======================================================

logger = getLogger(__name__)


def generate_token(user, new_email):
    """
    Generates a time-limited JWT token for verifying an email change request.
    Returns: A signed JWT token containing the user's ID, the new email, and an expiration timestamp.
    Notes: The token is intended for one-time use in the email verification flow.
    """
    from jwt import encode
    payload = {"user_id": user.id, "new_email": new_email, "exp": timezone.now() + timedelta(hours=24)}
    return encode(payload, settings.SECRET_KEY, algorithm="HS256")


def generate_access_token(user):
    """
    Generate a short-lived access token for stateless verification links.
    """
    return AccessToken.for_user(user)


def store_pending_user(data: dict):
    """
    Generate a UUID-based token and store user registration data in Redis for 15 minutes.
    """
    try:
        token = f"pending-user:{uuid.uuid4()}"
        cache.set(token, json.dumps(data), timeout=settings.CACHE_TTL)
        return token
    except Exception as error:
        logger.error(f"Failed to store pending user: {error}")
        raise CustomRedisException("Redis failed to store token", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_verification_email(user_data: dict, token: str, payload=None):
    """
    Send a verification email containing a tokenized link to the user's email address.
    """
    try:
        domain = settings.FRONTEND_DOMAIN
        query_params = {"token": token}
        if payload:
            query_params.update(payload)
        query_string = urlencode(query_params)
        verification_link = f"http://{domain}/users/verify-email?{query_string}"
        email = payload["email"] if payload else user_data["email"]
        subject = "تاییدیه ایمیل"
        message = f"روی لینک کلیک کنید تا ایمیل شما تایید شود: {verification_link}"
        html_content = f"""<p>درود<br>{user_data['first_name']} {user_data['last_name']} عزیز,
        <br><br>لطفا روی لینک زیر کلیک کنید تا ایمیل شما تایید شود:
        <br><a href="{verification_link}">تایید ایمیل</a><br><br>ممنون</p>"""
        email_sender(subject, message, html_content, [email])
    except Exception as error:
        logger.error(f"Failed to send verification email: {error}")
        raise CustomEmailException("Email failed to send")


def reset_password_email(user):
    """
    Send a password reset email to the user's email address.
    """
    try:
        domain = settings.FRONTEND_DOMAIN
        token = generate_access_token(user)
        query_params = {"token": str(token)}
        query_string = urlencode(query_params)
        verification_link = f"http://{domain}/users/set-new-password?{query_string}"
        subject = "Password Reset Request"
        message = f"روی لینک کلیک کنید تا رمز خود را بازیابی کنید: {verification_link}"
        html_content = f"""<p>درود<br>{user.first_name} {user.last_name} عزیز,
        <br><br>روی لینک زیر کلیک کنید تا رمز خود را بازیابی کنید:
        <br><a href="{verification_link}">بازیابی رمز عبور</a><br><br>ممنون</p>"""
        email_sender(subject, message, html_content, [user.email])
    except Exception as error:
        logger.error(f"Failed to send verification email to {user.email}: {error}")
        raise


#======================================== Sign Up View ===============================================

# Redis-first strategy
class SignUpAPIView(APIView):
    
    @extend_schema(
        request=CustomUserSerializer,
        responses={
            201: "Verification email sent successfully",
            409: "Username or email already exists",
            400: "Invalid registration data"
        },
        summary="Register a new user and send verification email.",
        description=(
            "Temporarily stores user registration data in Redis and sends a verification email. "
            "User data is persisted to the database only after successful email verification. "
            "Ensures username and email uniqueness before proceeding."
        ),
        parameters=[
            OpenApiParameter(name="username", type=OpenApiTypes.STR, required=True, description="Unique username for the new user account."),
            OpenApiParameter(name="first_name", type=OpenApiTypes.STR, required=True, description="User's first name."),
            OpenApiParameter(name="last_name", type=OpenApiTypes.STR, required=True, description="User's last name."),
            OpenApiParameter(name="email", type=OpenApiTypes.STR, required=True, description="Valid and unique email address for account verification."),
            OpenApiParameter(name="password", type=OpenApiTypes.STR, required=True, description="Password for the new account."),
            OpenApiParameter(name="re_password", type=OpenApiTypes.STR, required=True, description="Password confirmation to ensure accuracy."),
        ],
    )
    
    def post(self, request: Request):
        username = request.data.get("username")
        email = request.data.get("email")
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "این نام کاربری وحود دارد، نام کاربری دیگری انتخاب کنید."}, status=status.HTTP_409_CONFLICT)
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "ایمل مورد نظر قبلا ثبت نام کرده است."}, status=status.HTTP_409_CONFLICT)
        
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            token = store_pending_user(serializer.validated_data)
            send_verification_email(serializer.validated_data, token)
            return Response({"message": "لینک تایید به ایمیل شما ارسال شد."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# DB strategy
# class SignUpAPIView(APIView):
    
#     @extend_schema(
#         request=CustomUserSerializer,
#         responses={
#             201: "User registered successfully",
#             409: "Username or email already exists",
#             400: "Invalid data"
#         },
#         summary="API view for handling user registration requests.",
#         description=(
#             "Handles user registration by validating input data and creating a new user account. "
#             "Ensures the uniqueness of username and email, and triggers an email verification process upon successful registration."
#         ),
#         parameters=[
#             OpenApiParameter(name="username", type=OpenApiTypes.STR, required=True, description="Unique username for the new user account."),
#             OpenApiParameter(name="first_name", type=OpenApiTypes.STR, required=True, description="User's first name."),
#             OpenApiParameter(name="last_name", type=OpenApiTypes.STR, required=True, description="User's last name."),
#             OpenApiParameter(name="email", type=OpenApiTypes.STR, required=True, description="Valid and unique email address for account verification."),
#             OpenApiParameter(name="password", type=OpenApiTypes.STR, required=True, description="Password for the new account."),
#             OpenApiParameter(name="re_password", type=OpenApiTypes.STR, required=True, description="Password confirmation to ensure accuracy."),
#         ],
#     )

#     def post(self, request: Request):
#         username = request.data.get("username")
#         email = request.data.get("email")
#         if CustomUser.objects.filter(username=username).exists():
#             return Response({"error": "این نام کاربری وحود دارد، نام کاربری دیگری انتخاب کنید."}, status=status.HTTP_409_CONFLICT)
#         if CustomUser.objects.filter(email=email).exists():
#             return Response({"error": "ایمل مورد نظر قبلا ثبت نام کرده است."}, status=status.HTTP_409_CONFLICT)

#         serializer = CustomUserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             confirm_email_address(user)
#             return Response({"message": "اطلاعات شما ثبت شد، برای تکمیل فرایند ثبت نام به ایمیل خود بروید و ایمیل خود را تایید کنید."}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#======================================= Resend Verification Email View ==============================

# DB strategy
# class ResendVerificationEmailAPIView(APIView):

#     @extend_schema(
#         request=None,
#         responses={
#             200: "Verification email resent",
#             404: "Username not found"
#         },
#         summary="API view for resending verification email to the user.",
#         description=(
#             "Allows users to request a resend of the verification email if their account has not yet been activated. " 
#             "Validates the existence of the username and checks activation status before resending the email."
#         ),
#         parameters=[
#             OpenApiParameter(name="username", type=OpenApiTypes.STR, required=True, description="Unique username for the new user account."),
#         ],
#     )
    
#     def post(self, request: Request):
#         try:
#             username = request.data.get("username")
#             user = CustomUser.objects.get(username=username)
#             if user.is_active:
#                 return Response({"message": "ایمیل شما قبلا تایید شده است."}, status=status.HTTP_200_OK)
#             confirm_email_address(user)
#             return Response({"message": "ایمیل تایید دوباره برای شما ارسال شد."}, status=status.HTTP_200_OK)
#         except CustomUser.DoesNotExist:
#             return Response({"error": "نام کاربری مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
      
    
#======================================= Verify Email View ===========================================

class VerifyEmailAPIView(APIView):
    
    @extend_schema(
        request=None,
        responses={
            200: "Email address updated successfully.",
            201: "User account created and verified successfully.",
            400: "Invalid or expired token.",
            404: "User not found.",
            500: "Internal server error.",
        },
        summary="Verify email for signup or email change.",
        description=(
            "Handles email verification for two flows:\n\n"
            "1. **Signup Verification**: If no `email` parameter is present, the system assumes this is a new user registration. "
            "It retrieves pending user data from Redis using the provided token, creates the user account, and activates it.\n\n"
            "2. **Email Change Verification**: If an `email` parameter is present, the system assumes this is an email update. "
            "It decodes the token to identify the user and updates their email address accordingly.\n\n"
            "Handles token expiration, malformed data, and missing users gracefully."
        ),
    )

    def get(self, request: Request):
        token = request.GET.get("token")
        if not token:
            return Response({"error": "توکن یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)

        email = request.GET.get("email")

        try:
            if email:
                # Email change flow
                payload = AccessToken(token).payload
                user_id = payload.get("user_id")
                if not user_id:
                    return Response({"error": "توکن معتبر نیست یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    user = CustomUser.objects.get(pk=user_id)
                    user.email = email
                    user.save()
                    logger.info(f"Email changed for user {user.username}")
                    return Response({"message": "ایمیل جدید شما ثبت شد."}, status=status.HTTP_200_OK)
                except CustomUser.DoesNotExist:
                    return Response({"error": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)

            else:
                # Signup flow
                raw_data = cache.get(token)
                if not raw_data:
                    return Response({"error": "توکن منقضی شده یا نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    user_data = json.loads(raw_data)
                    user_data.pop("re_password", None)
                    user = CustomUser.objects.create_user(**user_data)
                    user.is_active = True
                    user.save()
                    cache.delete(token)
                    logger.info(f"New user registered: {user.username}")
                    return Response({"message": "ثبت نام شما با موفقیت انجام شد."}, status=status.HTTP_201_CREATED)
                except Exception as error:
                    logger.error(f"User creation failed: {error}")
                    return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except (InvalidToken, TokenError):
            return Response({"error": "توکن معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST)

            
#======================================= Login View ==================================================

class LoginAPIView(APIView):

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: "Successful login, token returned", 
            400: "Invalid credentials or data"
        },
        summary="API view for authenticating a user and returning a token.",
        description=(
            "Authenticates user credentials and returns a JWT access token upon successful login. "
            "Validates input data and handles incorrect credentials or malformed requests with appropriate error responses."
            ),
        parameters=[
            OpenApiParameter(name="username", type=OpenApiTypes.STR, required=True, description="Unique username for the new user account."),
            OpenApiParameter(name="password", type=OpenApiTypes.STR, required=True, description="Password for the new account."),
        ],
    )
    
    def post(self, request: Request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                # token = RefreshToken.for_user(user).access_token
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                return Response({"access": str(access), "refresh": str(refresh)}, status=status.HTTP_200_OK)
            return Response({"error": "نام کاربری و یا رمز عبور اشتباه است."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            

#======================================= User Profile View ===========================================

class UserProfileAPIView(APIView):

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            201: "User profile created successfully.",
            400: "Invalid input data. Check required fields and formats."
        },
        summary="Create or update a user's profile with additional personal information.",
        description=(
            "This endpoint allows authenticated users to submit or update their profile details, "
            "including phone number, gender, address, bio, and profile picture. "
            "The request must include a valid phone number and gender. "
            "Optional fields such as address, bio, and picture can be provided to enrich the user's profile."
        ),
        parameters=[
            OpenApiParameter(name="phone", type=OpenApiTypes.STR, required=True, description="User's unique phone number. Must not be associated with another account."),
            OpenApiParameter(name="gender", type=OpenApiTypes.STR, required=True, description="Gender identity of the user. Accepted values: 'male', 'female', 'other'."),
            OpenApiParameter(name="address", type=OpenApiTypes.STR, required=False, description="Optional physical address for the user."),
            OpenApiParameter(name="bio", type=OpenApiTypes.STR, required=False, description="Optional short biography or personal description."),
            OpenApiParameter(name="picture", type=OpenApiTypes.BINARY, required=False, description="Optional profile image. Must be a valid image file."),
        ],
    )

    def post(self, request: Request):
        data = request.data.copy()
        data["user"] = request.user.id
        serializer = UserProfileSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "اطلاعات شما ذخیره شد."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
#======================================= Update User View ============================================

class UpdateUserAPIView(APIView):

    permission_classes = [CheckOwnershipPermission]
    
    @extend_schema(
        request=PartialUserUpdateSerializer,
        responses={
            201: "User information updated successfully.",
            400: "Invalid input data. Check required fields and formats."
        },
        summary="Update user account information.",
        description=(
            "This endpoint allows authenticated users to update their account details. "
            "All fields are optional and will only be updated if provided. "
            "Password updates require both 'password' and 're_password' fields to match. "
        ),
        parameters=[
            OpenApiParameter(name="username", type=OpenApiTypes.STR, required=False, description="User's username. Optional."),
            OpenApiParameter(name="first_name", type=OpenApiTypes.STR, required=False, description="User's first name. Optional."),
            OpenApiParameter(name="last_name", type=OpenApiTypes.STR, required=False, description="User's last name. Optional."),
            OpenApiParameter(name="password", type=OpenApiTypes.STR, required=False, description="New password. Must be confirmed using 're_password'."),
            OpenApiParameter(name="re_password", type=OpenApiTypes.STR, required=False,description="Password confirmation. Must match 'password'."),
        ],
    )
    
    def put(self, request: Request):
        user = request.user
        self.check_object_permissions(request, user)
        serializer = PartialUserUpdateSerializer(data=request.data, instance=user, partial=True)
        if serializer.is_valid():
            data = serializer.save()
            return Response({
                "message": "اطلاعات شما با موفقیت تغییر کرد.",               
                "username": data.username, 
                "first_name": data.first_name, 
                "last_name": data.last_name, 
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#======================================= Request Email Change View =====================================

class RequestEmailChangeAPIView(APIView):
    
    permission_classes = [CheckOwnershipPermission]
    throttle_classes = [EmailChangeThrottle]
    
    @extend_schema(
        request=RequestEmailChangeSerializer,
        responses={
            200: "Verification email sent successfully.",
            400: "Invalid input data. Check email format.",
        },
        summary="Initiate email change request for authenticated user.",
        description=(
            "Allows authenticated users to request an email address change. "
            "The new email must be valid and not already registered. "
            "If the request is valid, a verification link is sent to the new email address. "
            "The change will only take effect after the user verifies the new email via the link."
        ),
        parameters=[
            OpenApiParameter(name="new_email", type=OpenApiTypes.STR, required=True, description="The new email address the user wants to use. Must be valid and not already registered."),
        ],
    )

    def post(self, request):
        self.check_object_permissions(request, request.user)
        serializer = RequestEmailChangeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = CustomUser.objects.get(pk=request.user.pk)
            except CustomUser.DoesNotExist:
                return Response({"error": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
            new_email = serializer.validated_data["new_email"]
            token = generate_access_token(user)
            user_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                }
            payload = {"email": new_email}
            send_verification_email(user_data, token, payload)
            return Response({"message": "لینک تأیید به ایمیل جدید ارسال شد و تا ۳۰ دقیقه معتبر است."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#======================================= Forget Password View ========================================

class PasswordResetAPIView(APIView):

    throttle_classes = [PasswordResetThrottle]
    
    @extend_schema(
        request=PasswordResetSerializer,
        responses={
            200: "Password reset email sent successfully.",
            400: "Invalid input data. Check email format.",
            404: "No user found with the provided email address."
        },
        summary="API view for requesting a password reset email.",
        description=(
            "This endpoint allows users to initiate a password reset by submitting their registered email address. "
            "If the email exists in the system, a password reset link will be sent to that address. "
            "Otherwise, a 404 error is returned. Email format is validated."
        ),
        parameters=[
            OpenApiParameter(name="email", type=OpenApiTypes.STR, required=True, description="Registered email address of the user requesting a password reset. Must be a valid format."),
        ],
    )
    
    def post(self, request: Request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({"error": "ایمیل وارد شده معتبر نمی باشد."}, status=status.HTTP_404_NOT_FOUND)
            reset_password_email(user)
            return Response({"message": "ایمیل برای تغییر رمز عبور ارسال شد."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(APIView):

    @extend_schema(
        request=SetNewPasswordSerializer,
        responses={
            201: "Password changed successfully.",
            400: "Invalid token or input data.",
            404: "User associated with the token was not found."
        },
        summary="API view for setting a new password using a reset token.",
        description=(
            "This endpoint allows users to set a new password using a valid token received via email. "
            "The token must be valid and not expired. If the token is valid, the user's password is updated. "
            "Both 'password' and 'token' fields are required. Token validation errors are handled explicitly."
        ),
         parameters=[
            OpenApiParameter(name="password", type=OpenApiTypes.STR, required=True, description="New password. Must be confirmed using 're_password'."),
            OpenApiParameter(name="re_password", type=OpenApiTypes.STR, required=True,description="Password confirmation. Must match 'password'."),
        ],
    )
    
    def post(self, request: Request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                password = serializer.validated_data["password"]
                token = serializer.validated_data["token"]
                payload = AccessToken(token).payload
                user_id = payload.get("user_id")
                if not user_id:
                    return Response({"error": "توکن معتبر نیست و یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
                user = CustomUser.objects.get(pk=user_id)
                user.set_password(password)
                user.save()
                return Response({"message": "رمز عبور با موفقیت تغییر کرد."}, status=status.HTTP_201_CREATED)
            except CustomUser.DoesNotExist:
                return Response({"error": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
            except InvalidToken:
                return Response({"error": "توکن معتبر نیست."}, status=status.HTTP_400_BAD_REQUEST)
            except TokenError:
                return Response({"error": "توکن منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as error:
                return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#======================================= Fetch Users View ============================================

class FetchUsersModelViewSet(viewsets.ModelViewSet):
    """ViewSet for fetching CustomUser instances with pagination and filtering."""
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all().order_by("id")
    serializer_class = FetchUsersSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ["id", "username", "first_name", "last_name"]
    lookup_field = "username"
    

#=====================================================================================================
#======================================= ArvanCloud View =============================================
#=====================================================================================================

class BucketFilesView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=None,
        responses={
            202: "Async task started successfully; task ID returned for polling",
            500: "Failed to dispatch task to Celery"
        },
        summary="Admin-only API view to trigger async file listing from ArvanCloud bucket.",
        description=(
            "Initiates a Celery task to asynchronously list all files stored in the ArvanCloud bucket. "
            "Only accessible to admin users. "
            "Returns immediately with a task ID and a polling URL to check task status and retrieve results once available.",
        ),
    )
        
    def get(self, request):
        logger.info("[BucketFilesView] Starting fetch_all_files task")
        try:
            task = fetch_all_files.apply_async()  
            logger.info(f"[BucketFilesView] Task sent to Celery with ID: {task.id}")
            return Response({
                "task_id": task.id,
                "status": "STARTED",
                "message": "File listing task started. Use task ID to check results.",
                "check_url": request.build_absolute_uri(
                reverse("bucket-files-result", kwargs={"task_id": task.id})
            ) 
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as error:
            logger.error(f"[BucketFilesView] Failed to send task to Celery: {error}", exc_info=True)
            return Response({
                "error": "Failed to start file listing task",
                "details": str(error)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
# ====================================

class BucketResultView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=None,
        responses={
            200: "Task completed successfully; file list returned",
            202: "Task still processing; retry suggested",
            400: "Missing or invalid task ID",
            500: "Task failed or result serialization error"
        },
        summary="Admin-only API view to poll results of async file listing task.",
        description=(
            "Checks the status and result of a previously triggered asynchronous file listing task in ArvanCloud. "
            "Accepts a task ID and returns one of the following: the completed file list, a pending status with retry suggestion, "
            "or error details if the task failed or result format is invalid. "
            "Only accessible to admin users."
        ),
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, required=True, description="Unique ID of the Celery task to poll for results.")
        ]
    )

    def get(self, request, task_id):
        task_id = str(task_id)
        
        if not task_id: 
            return Response({"error": "Task ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        result = AsyncResult(task_id)
        
        logger.info(f"[BucketResultView] Checking task result: {task_id}")
        
        if result.ready():
            if result.successful():
                try:
                    serializer = FileInfoSerializer(result.result, many=True)
                    logger.info(f"[BucketResultView] Task {task_id} completed successfully.")
                    return Response({
                        "status": "SUCCESS",
                        "task_id": task_id,
                        "files": serializer.data,
                        "count": len(result.result)
                    }, status=status.HTTP_200_OK)
                    
                except Exception as error:
                    logger.error(f"[BucketResultView] Serialization error for task {task_id}: {error}")
                    return Response({
                        "status": "ERROR",
                        "task_id": task_id,
                        "error": "Data format error",
                        "raw_result": str(result.result)[:500]  
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            else:
                logger.error(f"[BucketResultView] Task {task_id} failed: {result.result}")
                return Response({
                    "status": "FAILURE",
                    "task_id": task_id,
                    "error": str(result.result),
                    "traceback": result.traceback if hasattr(result, "traceback") else None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        logger.info(f"[BucketResultView] Task {task_id} still processing.")
        return Response({
            "status": "PENDING",
            "task_id": task_id,
            "message": "Task is still processing. Please check back later.",
            "suggested_retry": 2000  
        }, status=status.HTTP_202_ACCEPTED)


# ====================================

class FileDeleteView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=FileOperationSerializer,
        responses={
            202: "Delete task started successfully; task ID returned",
            400: "Invalid input data"
        },
        summary="Admin-only API view to delete a single file from the bucket.",
        description=(
            "Triggers an asynchronous Celery task to delete a specific file from the bucket. "
            "Accepts a file key and returns immediately with a task ID and polling URL to check deletion status."
        )
    )

    def post(self, request):
        serializer = FileOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        key = serializer.validated_data["key"]
        task = remove_file.delay(key)
        
        return Response({
            "task_id": task.id,
            "status": "STARTED",
            "message": f"Delete task started for file: {key}",
            "check_url": request.build_absolute_uri(
                reverse("file-delete-result", kwargs={"task_id": task.id})  
            )
        }, status=status.HTTP_202_ACCEPTED)


# ====================================

class BulkDeleteView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=BulkOperationSerializer,
        responses={
            202: "Bulk delete tasks started successfully; task IDs returned",
            400: "Invalid input or too many files"
        },
        summary="Admin-only API view to delete multiple files from the bucket.",
        description=(
            "Initiates asynchronous deletion tasks for up to 100 files in a single request. "
            "Accepts a list of file keys and returns a list of task IDs and polling URLs for each file deletion operation."
        )
    )

    def post(self, request):
        serializer = BulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        keys = serializer.validated_data["keys"]
        
        if len(keys) > 100: 
            return Response(
                {"error": "Maximum 100 files allowed in bulk operation"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task_ids = []
        for key in keys:
            task = remove_file.delay(key)
            task_ids.append({
                "key": key,
                "task_id": task.id,
                "status_url": request.build_absolute_uri(
                    reverse("file-delete-result", kwargs={"task_id": task.id})
                )
            })
        
        return Response({
            "operations": task_ids,
            "total_files": len(keys),
            "message": f"Started deletion of {len(keys)} files"
        }, status=status.HTTP_202_ACCEPTED)


# ====================================

class FileDeleteResultView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=None,
        responses={
            200: "File deleted successfully",
            202: "Delete task still processing",
            500: "Task failed or encountered an error"
        },
        summary="Admin-only API view to check the result of a file deletion task.",
        description=(
            "Polls the status of a previously triggered file deletion task using its task ID. "
            "Returns success, failure, or pending status along with relevant details or error tracebacks."
        ),
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, required=True, description="Unique ID of the Celery task to poll for deletion result.")
        ]
    )
    
    def get(self, request, task_id):
        task_id = str(task_id)
        result = AsyncResult(task_id)
        
        logger.info(f"[FileDeleteResultView] Checking task result: {task_id}")
        
        if result.ready():
            if result.successful():
                logger.info(f"[FileDeleteResultView] Task {task_id} completed successfully.")
                return Response({
                    "status": "SUCCESS",
                    "task_id": task_id,
                    "message": "File deleted successfully",
                    "result": result.result  
                }, status=status.HTTP_200_OK)
                
            else:
                logger.error(f"[FileDeleteResultView] Task {task_id} failed: {result.result}")
                return Response({
                    "status": "FAILURE", 
                    "task_id": task_id,
                    "error": str(result.result),
                    "traceback": result.traceback
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        logger.info(f"[FileDeleteResultView] Task {task_id} still processing.")
        return Response({
            "status": "PENDING",
            "task_id": task_id,
            "message": "Delete operation still in progress"
        }, status=status.HTTP_202_ACCEPTED)


# ====================================

class FileDownloadView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=FileOperationSerializer,
        responses={
            202: "Download task started successfully; task ID returned",
            400: "Invalid input data"
        },
        summary="Admin-only API view to initiate file download from bucket.",
        description=(
            "Triggers an asynchronous Celery task to download a file from the bucket to a specified local path. "
            "If no path is provided, a default location is used. Returns a task ID and polling URL to check download status."
        )
    )

    def post(self, request):
        serializer = FileOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        key = serializer.validated_data["key"]
        local_path = serializer.validated_data.get("local_path")
        
        if not local_path:
            filename = os.path.basename(key)
            local_path = os.path.join("/app/shared_downloads/", filename)
        elif local_path.endswith("/"):
            filename = os.path.basename(key)
            local_path = os.path.join(local_path, filename)
        
        task = download_obj.delay(key, local_path)
    
        return Response({
            "task_id": task.id,
            "status": "STARTED",
            "message": f"Download task started for file: {key}",
            "check_url": request.build_absolute_uri(
                reverse("file-download-result", kwargs={"task_id": task.id})
            )
        }, status=status.HTTP_202_ACCEPTED)
    

# ====================================

class FileDownloadResultView(APIView):
    
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        request=None,
        responses={
            200: "File downloaded successfully and returned as attachment",
            202: "Download task still processing",
            404: "Downloaded file not found",
            500: "Task failed or file retrieval error"
        },
        summary="Admin-only API view to retrieve the result of a file download task.",
        description=(
            "Polls the status of a previously triggered file download task using its task ID. "
            "If successful, returns the downloaded file as an attachment. "
            "Handles pending, failed, or missing file scenarios with appropriate responses."
        ),
        parameters=[
            OpenApiParameter(name="task_id", type=OpenApiTypes.STR, required=True, description="Unique ID of the Celery task to poll for download result.")
        ]
    )

    def get(self, request, task_id):
        result = AsyncResult(str(task_id))  
        
        if result.ready():
            if result.successful():
                file_path = result.result
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as file:
                            file_content = file.read()
                        
                        response = HttpResponse(file_content)
                        response["Content-Type"] = "image/jpeg"
                        response["Content-Disposition"] = f"attachment; filename='{os.path.basename(file_path)}'"
                        
                        os.remove(file_path)
                        return response
                        
                    except Exception as error:
                        logger.error(f"File download failed: {error}")
                        return Response(
                            {"error": "File download failed"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                return Response(
                    {"error": "File not found after download"},
                    status=status.HTTP_404_NOT_FOUND
                )
            else:
                return Response({
                    "status": "FAILED",
                    "error": str(result.result),
                    "traceback": result.traceback
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "status": "PENDING",
            "message": "Download still in progress"
        }, status=status.HTTP_202_ACCEPTED)
        
      
#=====================================================================================================