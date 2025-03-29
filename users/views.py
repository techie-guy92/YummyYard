from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from logging import getLogger
from .models import *
from .serializers import *
from utilities import email_sender
from custom_permission import CheckOwnershipPermission


#======================================== email senders ==============================================

logger = getLogger("email-senders")


def confirm_email_address(user):
    """
    Send a verification email to the user's email address.

    Parameters:
    user (CustomUser): The user to send the verification email to
    """
    
    try:
        token = RefreshToken.for_user(user).access_token
        domain = "127.0.0.1:8000"
        verification_link = f"http://{domain}/users/verify-email?token={str(token)}"
        subject = "Verify your email"
        message = f"Click on the link to verify your email: {verification_link}"
        html_content = f"""<p>Hello dear {user.first_name} {user.last_name},
        <br><br>Please click on the link below to verify your email address:
        <br><a href='{verification_link}'>Verify Email</a><br><br>Thank you!</p>"""
        email_sender(subject, message, html_content, [user.email])
    except Exception as error:
        logger.error(f"Failed to send verification email to {user.email}: {error}")
        raise
    

def reset_password_email(user):
    """
    Send a password reset email to the user's email address.

    Parameters:
    user (CustomUser): The user to send the password reset email to
    """
    
    try:
        token = AccessToken.for_user(user)
        domain = "127.0.0.1:8000"
        verification_link = f"http://{domain}/users/set-new-password?token={str(token)}"
        subject = "Password Reset Request"
        message = f"Click on the link to reset your password: {verification_link}"
        html_content = f"""<p>Hello dear {user.first_name} {user.last_name},
        <br><br>Please click on the link below to reset your password:
        <br><a href='{verification_link}'>Reset Password</a><br><br>Thank you!</p>"""
        email_sender(subject, message, html_content, [user.email])
    except Exception as error:
        logger.error(f"Failed to send verification email to {user.email}: {error}")
        raise
    

#======================================== Sign Up View ===============================================

class SignUpAPIView(APIView):
    """
    API view for handling user registration requests.
    """
    
    @extend_schema(
        request=CustomUserSerializer,
        responses={201: "User registered successfully", 409: "Username or email already exists", 400: "Invalid data"}
    )
    def post(self, request: Request):
        """
        Handle POST requests for user registration.

        Parameters:
        request (Request): The request object containing user registration data

        Returns:
        Response: The response object with appropriate status and message
        """
        username = request.data.get("username")
        email = request.data.get("email")
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "این نام کاربری وحود دارد، نام کاربری دیگری انتخاب کنید."}, status=status.HTTP_409_CONFLICT)
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "ایمل مورد نظر قبلا ثبت نام کرده است."}, status=status.HTTP_409_CONFLICT)

        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            confirm_email_address(user)
            return Response({"message": "اطلاعات شما ثبت شد، برای تکمیل فرایند ثبت نام به ایمیل خود بروید و ایمیل خود را تایید کنید."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

#======================================= Resend Verification Email View ==============================

class ResendVerificationEmailAPIView(APIView):
    """
    API view for resending verification email to the user.
    """
    
    @extend_schema(
        request=None,
        responses={200: "Verification email resent", 404: "Username not found"}
    )
    def post(self, request: Request):
        """
        Handle POST requests to resend verification email.

        Parameters:
        request (Request): The request object containing the username

        Returns:
        Response: The response object with appropriate status and message
        """
        try:
            username = request.data.get("username")
            user = CustomUser.objects.get(username=username)
            if user.is_active:
                return Response({"message": "ایمیل شما قبلا تایید شده است."}, status=status.HTTP_200_OK)
            confirm_email_address(user)
            return Response({"message": "ایمیل تایید دوباره ارسال شد."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "نام کاربری مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
      
    
#======================================= Verify Email View ===========================================

class VerifyEmailAPIView(APIView):
    """
    API view for verifying user's email using the token provided.
    """
    
    @extend_schema(
        request=None,
        responses={200: "Email verified successfully", 202: "User already verified", 400: "Invalid or expired token", 404: "User not found"}
    )
    def get(self, request: Request):
        """
        Handle GET requests to verify user's email.

        Parameters:
        request (Request): The request object containing the token

        Returns:
        Response: The response object with appropriate status and message
        """
        try:
            token = request.GET.get("token")
            payload = AccessToken(token).payload
            user_id = payload.get("user_id")
            if not user_id:
                return Response({"error": "توکن معتبر نیست یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = CustomUser.objects.get(pk=user_id)
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return Response({"message": "ثبت نام شما کامل شد."}, status=status.HTTP_200_OK)
                return Response({"message": f"کاربر {user.username} قبلا تایید شده است."}, status=status.HTTP_202_ACCEPTED)
            except CustomUser.DoesNotExist:
                return Response({"error": "کاربر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)
        except InvalidToken:
            return Response({"error": "توکن معنبر نیست."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "توکن معنبر نیست."}, status=status.HTTP_400_BAD_REQUEST)
        

#======================================= Login View ==================================================

class LoginAPIView(APIView):
    """
    API view for authenticating a user and returning a token.
    """
    
    @extend_schema(
        request=LoginSerializer,
        responses={200: "Successful login, token returned", 400: "Invalid credentials or data"}
    )
    def post(self, request: Request):
        """
        Handle POST requests for user login.

        Parameters:
        request (Request): The request object containing login credentials

        Returns:
        Response: The response object with the token if successful, otherwise an error message
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                token = RefreshToken.for_user(user).access_token
                return Response({"token": str(token)}, status=status.HTTP_200_OK)
            return Response({"error": "نام کاربری و یا رمز عبور اشتباه است."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            
#======================================= User Profile View ===========================================

class UserProfileAPIView(APIView):
    """
    API view for adding additional information to a user's account.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=UserProfileSerializer,
        responses={201: "User data added successfully", 400: "Invalid data"}
    )
    def post(self, request: Request):
        """
        Handle POST requests to add additional user information.

        Parameters:
        request (Request): The request object containing user profile data

        Returns:
        Response: The response object with appropriate status and message
        """
        data = request.data.copy()
        data["user"] = request.user.id
        serializer = UserProfileSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "اطلاعات شما ذخیره شد."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
#======================================= Update User View ============================================

class UpdateUserAPIView(APIView):
    """
    API view for handling user information update requests.

    Attributes:
    permission_classes (list): List of permissions required for this view, including CheckOwnershipPermission to ensure the requesting user is the same as the user being updated.
    """
    
    permission_classes = [CheckOwnershipPermission]
    
    @extend_schema(
        request=UpdateUserSerializer,
        responses={201: "User data updated successfully", 400: "Invalid data"}
    )
    def put(self, request: Request):
        """
        Handle user information update requests.

        Parameters:
        request (Request): The request object containing user data

        Returns:
        Response: The response object indicating success or failure
        """
        user = request.user
        self.check_object_permissions(request, user)
        serializer = UpdateUserSerializer(data=request.data, instance=user, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "اطلاعات شما با موفقیت تغییر کرد."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#======================================= Forget Password View ========================================

class PasswordResetAPIView(APIView):
    """
    API view for handling password reset requests.

    Attributes:
    @extend_schema: Schema information for request and response
    """
    
    @extend_schema(
        request=PasswordResetSerializer,
        responses={200: "Password reset email sent", 400: "Invalid data", 404: "Email not found"}
    )
    def post(self, request: Request):
        """
        Handle password reset email requests.

        Parameters:
        request (Request): The request object containing user email

        Returns:
        Response: The response object indicating success or failure
        """
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            if CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.get(email=email)
                reset_password_email(user)
                return Response({"message": "ایمیل برای تغییر رمز عبور ارسال شد."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "ایمیل وارد شده معتبر نمی باشد."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(APIView):
    """
    API view for setting a new password using a token.

    Attributes:
    @extend_schema: Schema information for request and response
    """
    
    @extend_schema(
        request=SetNewPasswordSerializer,
        responses={201: "Password changed successfully", 400: "Invalid data or token", 404: "User not found"}
    )
    def post(self, request: Request):
        """
        Verify user's email using the token provided and set a new password.

        Parameters:
        request (Request): The request object containing new password and token

        Returns:
        Response: The response object indicating success or failure
        """
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
    """
    ViewSet for fetching CustomUser instances with pagination and filtering.

    Attributes:
    permission_classes (list): List of permissions required for this view
    queryset (QuerySet): The queryset of CustomUser objects
    serializer_class (Serializer): The serializer class to use
    pagination_class (Pagination): The pagination class to use
    filter_backends (list): List of filter backends to use
    search_fields (list): List of fields to search
    lookup_field (str): The field to use for lookups
    """
    
    permission_classes = [IsAdminUser]
    queryset = CustomUser.objects.all().order_by("id")
    serializer_class = FetchUsersSerializer
    pagination_class = PageNumberPagination
    filter_backends = [SearchFilter]
    search_fields = ["id", "username", "first_name", "last_name"]
    lookup_field = "username"
    
    
#=====================================================================================================