import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
import django
django.setup()

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from jwt import decode
from django.urls import resolve, reverse
from django.core import mail
from unittest.mock import patch
from .models import *
from .serializers import *
from .views import *
from .urls import *
from users_constant import primary_user_1, primary_user_2, primary_user_3, primary_user_4, new_user_1, invalid_user_1
from utilities import create_test_users


#======================================== Sign Up Test =============================================

class SignUpTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("sign-up")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
   
    def test_customer_model(self):
        self.assertEqual(self.user_1.username, primary_user_1["username"])
        self.assertEqual(self.user_1.user_type, "user")
        self.assertTrue(self.user_1.is_active)
        self.assertTrue(self.user_1.is_admin)
        self.assertTrue(self.user_1.is_superuser)
        self.assertFalse(self.user_1.is_premium)
        self.assertTrue(self.user_2.is_active)
        self.assertTrue(self.user_2.is_premium)
        self.assertFalse(self.user_2.is_admin)
        self.assertFalse(self.user_2.is_superuser)
        self.assertFalse(self.user_4.is_active)
        
    def test_customer_serializer(self):
        serializer_1 = CustomUserSerializer(self.user_1)
        serializer_2 = CustomUserSerializer(self.user_2)
        serializer_4 = CustomUserSerializer(self.user_4)
        ser_data_1 = serializer_1.data 
        ser_data_2 = serializer_2.data 
        ser_data_4 = serializer_4.data
        self.assertIn("is_admin", ser_data_1)
        self.assertIn("is_superuser", ser_data_1)
        self.assertNotIn("is_active", ser_data_1)
        self.assertNotIn("is_premium", ser_data_1)
        self.assertEqual(ser_data_1["username"], primary_user_1["username"])
        self.assertTrue(ser_data_1["is_admin"])
        self.assertTrue(ser_data_1["is_superuser"])
        self.assertFalse(ser_data_2["is_admin"])
        self.assertFalse(ser_data_2["is_superuser"])
        self.assertFalse(ser_data_4["is_admin"])
        self.assertFalse(ser_data_4["is_superuser"])
         
    def test_signup_view(self):
        response = self.client.post(self.url, new_user_1, format="json")
        user = CustomUser.objects.get(username=new_user_1["username"])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "اطلاعات شما ثبت شد، برای تکمیل فرایند ثبت نام به ایمیل خود بروید و ایمیل خود را تایید کنید.")
        self.assertTrue(user.check_password(new_user_1["password"]))
        self.assertEqual(user.email, new_user_1["email"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [new_user_1["email"]])
        self.assertIn("Verify your email", mail.outbox[0].subject)
        self.assertIn("Click on the link to verify your email", mail.outbox[0].body)

    def test_signup_with_invalid_data(self):
        response = self.client.post(self.url, invalid_user_1, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("password", response.data)
    
    def test_signup_url(self):
        view = resolve("/users/sign-up/")
        self.assertEqual(view.func.cls, SignUpAPIView)

    
#======================================== Resend Verification Email Test ===========================

# class ResendVerificationEmailTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.url = reverse("resend-verification-email")
#         self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        
#     @patch("users.views.confirm_email_address")    
#     def test_resend_verification_email_view(self,  mock_confirm_email_address):
#         user = {"username": primary_user_4["username"]}
#         response = self.client.post(self.url, user, format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["message"], "ایمیل تایید دوباره ارسال شد.")
#         mock_confirm_email_address.assert_called_once_with(self.user_4)
    
#     def test_already_verified_view(self):
#         user = {"username": primary_user_2["username"]}
#         response = self.client.post(self.url, user, format="json")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["message"], "ایمیل شما قبلا تایید شده است.")
    
#     def test_email_not_found_view(self):
#         user = {"username": new_user_1["username"]}
#         response = self.client.post(self.url, user, format="json")
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#         self.assertEqual(response.data["error"], "نام کاربری مورد نظر یافت نشد.")
    
#     def test_resend_verification_email_url(self):
#         view = resolve("/users/resend-verification-email/")
#         self.assertEqual(view.func.cls, ResendVerificationEmailAPIView)
        
        
#======================================== Verify Email Test ========================================

class VerifyEmailTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("verify-email")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.token_1 = str(RefreshToken.for_user(self.user_1).access_token)
        self.token_2 = str(RefreshToken.for_user(self.user_2).access_token)
        self.token_4 = str(RefreshToken.for_user(self.user_4).access_token)
        
    def test_verify_email_view(self):
        token = {"token": self.token_4}
        response = self.client.get(self.url, token, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "ثبت نام شما کامل شد.")
    
    def test_already_verified_view(self):
        token = {"token": self.token_2}
        response = self.client.get(self.url, token, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["message"], f"کاربر {self.user_2.username} قبلا تایید شده است.")
    
    def test_verify_email_url(self):
        view = resolve("/users/verify-email/")
        self.assertEqual(view.func.cls, VerifyEmailAPIView)
        
        
#======================================== Login Test ===============================================

class LoginTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.login_data = {"username": primary_user_2["username"], "password": primary_user_2["password"]}
        self.invalid_login_data = {"username": new_user_1["username"], "password": new_user_1["password"]}
        
    def test_login_serializer(self):
        serializer = LoginSerializer(data=self.login_data)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.data
        self.assertIn("username", serializer_data)
        self.assertNotIn("password", serializer_data)
    
    def test_login_view(self):
        response = self.client.post(self.url, self.login_data, format="json")
        decode_token = decode(response.data["token"], settings.SECRET_KEY, algorithms=["HS256"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(decode_token["user_id"], self.user_2.id)
        self.assertIn("token", response.data)
        
    def test_invalid_login_view(self):
        response = self.client.post(self.url, self.invalid_login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "نام کاربری و یا رمز عبور اشتباه است.")
    
    def test_login_url(self):
        view = resolve("/users/login/")
        self.assertEqual(view.func.cls, LoginAPIView)
        
        
#======================================== User Profile Test ========================================

class UserProfileTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("user-profile")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.client.force_authenticate(self.user_1)
        self.created_user_data = UserProfile.objects.create(
            user=self.user_1,  
            phone="09123469239",
            address="Tehran",
            gender="male",
            bio="I'm a full-stack developer"
        )
        
    def test_user_profile_model(self):
        self.assertEqual(str(self.created_user_data), f"{self.user_1.username} - {self.created_user_data.phone}")
    
    def test_user_profile_serializer(self):
        serializer = UserProfileSerializer(instance=self.created_user_data)
        ser_data= serializer.data
        self.assertEqual(ser_data["id"], self.created_user_data.id)
        self.assertIn("phone", ser_data)
    
    def test_user_profile_view(self):
        user_data = {
            "user": self.user_2.id, 
            "phone": "09213467612",
            "address": "Tehran",
            "gender": "other"
        }
        response = self.client.post(self.url, user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "اطلاعات شما ذخیره شد.")
    
    def test_user_profile_url(self):
        view = resolve("/users/user-profile/")
        self.assertEqual(view.func.cls, UserProfileAPIView)
        
        
#======================================== Update User Test =========================================

class UpdateUserTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("update-user")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.client.force_authenticate(self.user_2)
        self.update_data = {"first_name": "saghar", "last_name": "sharifi"}
        
    def test_update_user_serializer(self):
        serializer = PartialUserUpdateSerializer(data=self.update_data, instance=self.user_2, partial=True)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.save()
        ser_data = serializer.data
        self.assertEqual(ser_data["first_name"], self.update_data["first_name"])
        self.assertIn("last_name", self.update_data)
        
    def test_update_user_view(self):
        response = self.client.put(self.url, self.update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "اطلاعات شما با موفقیت تغییر کرد.")
    
    def test_update_user_url(self):
        view = resolve("/users/update-user/")
        self.assertEqual(view.func.cls, PartialUserUpdateAPIView)
        
        
#======================================== Password Reset Test ======================================

class PasswordResetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("password-reset")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
       
    @patch("users.views.reset_password_email")
    def test_password_reset_view(self, mock_reset_password_email):
        email = {"email": self.user_2.email}
        response = self.client.post(self.url, email, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "ایمیل برای تغییر رمز عبور ارسال شد.")
        mock_reset_password_email.assert_called_once_with(self.user_2)
    
    def test_password_reset_url(self):
        view = resolve("/users/password-reset/")
        self.assertEqual(view.func.cls, PasswordResetAPIView)
        

#======================================== Set New Password Test ====================================

class SetNewPasswordTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("set-new-password")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.user_data = {
            "password": "abcdABCD1234@",
            "re_password": "abcdABCD1234@",
            "token": str(RefreshToken.for_user(self.user_2).access_token)
        }
        
    def test_set_new_password_serializer(self):
        serializer = SetNewPasswordSerializer(data=self.user_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        self.assertEqual(validated_data["password"], self.user_data["password"])
        self.assertIn("password", validated_data)
        self.assertIn("token", validated_data)
    
    def test_set_new_password_view(self):
        response = self.client.post(self.url, self.user_data ,format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "رمز عبور با موفقیت تغییر کرد.")
    
    def test_set_new_password_invalid_view(self):
        invalid_user_data = {
            "password": "abcdABCD1234@",
            "re_password": "abcdABCD1234@",
            "token": "token"
        }
        response = self.client.post(self.url, invalid_user_data ,format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "توکن منقضی شده است.")
    
    def test_set_new_password_url(self):
        view = resolve("/users/set-new-password/")
        self.assertEqual(view.func.cls, SetNewPasswordAPIView)
        
        
#======================================== Fetch Users Test =========================================

class FetchUsersTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("fetch-users-list")
        self.user_1, self.user_2, self.user_3, self.user_4 = create_test_users()
        self.client.force_authenticate(self.user_1)
        
    def test_fetch_users_serializer(self):
        serializer = FetchUsersSerializer(instance=self.user_1)
        ser_data = serializer.data
        self.assertIn("username", ser_data)
        self.assertIn("is_active", ser_data)
    
    def test_fetch_users_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", [])
        self.assertEqual(len(results), 4)  
        for result, user in zip(results, [self.user_1, self.user_2, self.user_3, self.user_4]):
            self.assertEqual(result["username"], user.username)
            self.assertEqual(result["email"], user.email)
    
    def test_fetch_users_url(self):
        view = resolve("/users/fetch-users/")
        self.assertEqual(view.func.cls, FetchUsersModelViewSet)
        
        
#===================================================================================================