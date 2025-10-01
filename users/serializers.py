from rest_framework import serializers
from uuid import UUID
from .models import *
from utilities import *


#======================================= Custom User Serializer ====================================

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving CustomUser instances.

    Attributes:
    password (str): The password of the user (write-only)
    re_password (str): The repeated password for confirmation (write-only)
    """
    
    password = serializers.CharField(max_length=20, write_only=True, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True)
    email = serializers.EmailField(max_length=100, validators=[email_validator])
    
    class Meta:
        model = CustomUser
        # fields = ["username", "first_name", "last_name", "email", "password", "re_password", "is_admin", "is_superuser"]
        fields = ["username", "first_name", "last_name", "email", "password", "re_password"]
        
    def create(self, validated_data):        
        # is_admin = validated_data.pop("is_admin", False)        
        # is_superuser = validated_data.pop("is_superuser", False)        
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "وارد کردن رمز عبور ضروری است."})
        
        user = CustomUser.objects.create_user(
            username = validated_data["username"],
            first_name = validated_data["first_name"],
            last_name = validated_data["last_name"],
            email = validated_data["email"],
            password = password,
        )
        # user.is_admin = is_admin
        # user.is_superuser = is_superuser
        # if is_admin and is_superuser:
        #     user.user_type = "frontend"
        user.save()
        return user
    
    def validate(self, attrs):        
        if attrs["password"] != attrs["re_password"]:
            raise serializers.ValidationError("رمز عبور و تکرار آن یکسان نمی باشد.")
        return attrs

    
#======================================= Login Serializer ==========================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login.

    Attributes:
    username (str): The username of the user
    password (str): The password of the user (write-only)
    """
    
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=20, write_only=True)


#======================================= User Profile Serializers ==================================

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving UserProfile instances.
    """
    
    class Meta:
        model = UserProfile
        fields = "__all__"
        extra_kwargs = {"user": {"required": False}}


#======================================= Update User Serializer ====================================

class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating CustomUser instances.

    Attributes:
    password (str): The password of the user (write-only, optional)
    re_password (str): The repeated password for confirmation (write-only, optional)
    """
    
    password = serializers.CharField(max_length=20, write_only=True, required=False, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True, required=False)
    email = serializers.CharField(max_length=100, validators=[email_validator])
    
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "password", "re_password"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": False}
        }
        
    def update(self, instance, validated_data):
        """
        Updates an existing CustomUser instance.

        Parameters:
        instance (CustomUser): The existing user instance
        validated_data (dict): The validated data containing updated user details

        Returns:
        CustomUser: The updated user instance
        """
        
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
    def validate(self, attrs):
        """
        Validates the passwords and ensures they match.

        Parameters:
        attrs (dict): The attributes to validate

        Returns:
        dict: The validated attributes
        """
        
        instance = getattr(self, "instance", None)
        if not instance:
            raise serializers.ValidationError("کاربر مورد نظر یافت نشد.")
        if "password" in attrs and attrs["password"] != attrs.get("re_password"):
            raise serializers.ValidationError({"re_password": "رمز عبور و تکرار آن یکسان نمی باشد."})
        return attrs
    
    
#======================================= Forget Password Serializer ================================

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for handling password reset requests.

    Attributes:
    email (str): The email address of the user requesting the password reset
    """
    
    email = serializers.EmailField()


class SetNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password after a reset request.

    Attributes:
    password (str): The new password (write-only)
    re_password (str): The repeated new password for confirmation (write-only)
    token (str): The password reset token
    """
    
    password = serializers.CharField(max_length=20, write_only=True, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True)
    token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """
        Validates the new passwords and ensures they match.

        Parameters:
        attrs (dict): The attributes to validate

        Returns:
        dict: The validated attributes
        """
        
        if "password" not in attrs:
            raise serializers.ValidationError({"password": "وارد کردن رمز عبور ضروری است."})
        if attrs["password"] != attrs.get("re_password"):
            raise serializers.ValidationError({"re_password": "رمز عبور و تکرار آن یکسان نمی باشد."})
        return attrs
    
    def to_representation(self, instance):
        """
        Removes password fields from the representation.

        Parameters:
        instance (object): The instance to represent

        Returns:
        dict: The representation of the instance
        """
        
        data = super().to_representation(instance)
        data.pop("password", None)
        data.pop("re_password", None)
        return data
    
    
#======================================= Fetch Users Serializer ====================================

class FetchUsersSerializer(serializers.ModelSerializer):
    """
    Serializer for fetching CustomUser instances.
    """
    
    class Meta:
        model = CustomUser
        fields = "__all__"


#======================================= ArvanCloud Serializer =====================================

class FileOperationSerializer(serializers.Serializer):
    """
    Serializer for single file operations on the ArvanCloud bucket.

    Used to validate input for tasks such as deleting or downloading a file.
    - `key`: Required. The unique path of the file in the bucket.
    - `local_path`: Optional. Local destination path for downloaded files.
    """
    
    key = serializers.CharField(max_length=500, required=True)
    local_path = serializers.CharField(max_length=500, required=False, allow_null=True)


# ====================================

class BulkOperationSerializer(serializers.Serializer):
    """
    Serializer for bulk file operations on the ArvanCloud bucket.

    Used to validate a list of file keys for batch deletion.
    - `keys`: Required. A list of file paths to be deleted from the bucket.
    """
    
    keys = serializers.ListField(child=serializers.CharField(max_length=500),required=True)


# ====================================

class FileInfoSerializer(serializers.Serializer):
    """
    Serializer for representing metadata of files stored in the ArvanCloud bucket.

    Used to format the output of file listing tasks.
    - `Key`: The file's path in the bucket.
    - `Size`: File size in bytes.
    - `LastModified`: Timestamp of last modification.
    - `ETag`: Entity tag used for cache validation and versioning.
    """
    
    Key = serializers.CharField()
    Size = serializers.IntegerField()
    LastModified = serializers.DateTimeField()
    ETag = serializers.CharField()
    StorageClass = serializers.CharField(required=False)  

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
        return data
    
    
#===================================================================================================