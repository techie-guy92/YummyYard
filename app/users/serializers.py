from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from uuid import UUID
from .models import *
from utilities.utilities import *


#======================================= Custom User Serializer ====================================

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving CustomUser instances.
    """
    password = serializers.CharField(max_length=20, write_only=True, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True)
    username = serializers.CharField(max_length=30, validators=[
        UniqueValidator(queryset=CustomUser.objects.all(), message="این نام کاربری وجود دارد، نام کاربری دیگری انتخاب کنید.")
        ]
    )
    
    email = serializers.EmailField(max_length=100, validators=[
        email_validator, 
        UniqueValidator(queryset=CustomUser.objects.all(), message="ایمیل قبلا ثبت شده است.")
        ]
    )

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "password", "re_password"]
        
    def create(self, validated_data):              
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
        return user
    
    def validate(self, attrs):
        if attrs["password"] != attrs["re_password"]:
            raise serializers.ValidationError("رمز عبور و تکرار آن یکسان نمی باشد.")        
        return attrs

    
#======================================= Login Serializer ==========================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login.
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

class PartialUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating CustomUser instances.
    """
    password = serializers.CharField(max_length=20, write_only=True, required=False, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "password", "re_password"]
        
    def update(self, instance, validated_data): 
        instance.username = validated_data.get("username", instance.username)       
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    
    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if not instance:
            raise serializers.ValidationError("کاربر مورد نظر یافت نشد.")
        if "username" in attrs:
            new_username = attrs["username"]
            if CustomUser.objects.filter(username=new_username).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({"username": "نام کاربری قبلاً انتخاب شده است."})
        if "password" in attrs and attrs["password"] != attrs.get("re_password"):
            raise serializers.ValidationError({"re_password": "رمز عبور و تکرار آن یکسان نمی باشد."})
        return attrs


#======================================= Request Email Change Serializer ============================

class RequestEmailChangeSerializer(serializers.Serializer):
    """
    Serializer for handling email change requests.
    Validates the new email format and ensures it is not already registered.
    """
    new_email = serializers.EmailField(validators=[email_validator])

    def validate_new_email(self, attr):
        if CustomUser.objects.filter(email=attr).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return attr
    
    
#======================================= Forget Password Serializer ================================

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for handling password reset requests.
    """
    email = serializers.EmailField()


class SetNewPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password after a reset request.
    """
    password = serializers.CharField(max_length=20, write_only=True, validators=[password_validator])
    re_password = serializers.CharField(max_length=20, write_only=True)
    token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if "password" not in attrs:
            raise serializers.ValidationError({"password": "وارد کردن رمز عبور ضروری است."})
        if attrs["password"] != attrs.get("re_password"):
            raise serializers.ValidationError({"re_password": "رمز عبور و تکرار آن یکسان نمی باشد."})
        return attrs
    
    def to_representation(self, instance):
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

#===================================================================================================
#======================================= ArvanCloud Serializer =====================================
#===================================================================================================

class FileOperationSerializer(serializers.Serializer):
    """
    Serializer for single file operations on the ArvanCloud bucket.
    Used to validate input for tasks such as deleting or downloading a file.
    - key: Required. The unique path of the file in the bucket.
    - local_path: Optional. Local destination path for downloaded files.
    """
    key = serializers.CharField(max_length=500, required=True)
    local_path = serializers.CharField(max_length=500, required=False, allow_null=True)


# ====================================

class BulkOperationSerializer(serializers.Serializer):
    """
    Serializer for bulk file operations on the ArvanCloud bucket.
    Used to validate a list of file keys for batch deletion.
    - keys: Required. A list of file paths to be deleted from the bucket.
    """
    keys = serializers.ListField(child=serializers.CharField(max_length=500),required=True)


# ====================================

class FileInfoSerializer(serializers.Serializer):
    """
    Serializer for representing metadata of files stored in the ArvanCloud bucket.
    Used to format the output of file listing tasks.
    - Key: The file's path in the bucket.
    - Size: File size in bytes.
    - LastModified: Timestamp of last modification.
    - ETag: Entity tag used for cache validation and versioning.
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