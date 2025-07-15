from django.forms import ModelForm, ValidationError, CharField, PasswordInput, EmailField, EmailInput
from .models import CustomUser
from utilities import *


#======================================= Custom User Form ====================================

class CustomUserForm(ModelForm):
    password = CharField(label="Password", widget=PasswordInput(attrs={'placeholder': 'Enter a valid password'}, render_value=True), validators=[password_validator])
    re_password = CharField(label="Password Confirmation", widget=PasswordInput(attrs={'placeholder': 'Re-enter entered password'}, render_value=True))
    email = EmailField(label="Email", widget=EmailInput(attrs={'placeholder': 'Enter a valid email address'}), validators=[email_validator])

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "user_type"]
        
    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        if first_name:
            cleaned_data["first_name"] = first_name.capitalize()
        if last_name:
            cleaned_data["last_name"] = last_name.capitalize()
        return cleaned_data
    
    def clean_re_password(self):
        pass_1 = self.cleaned_data.get("password")
        pass_2 = self.cleaned_data.get("re_password")
        if pass_1 and pass_2 and pass_1 != pass_2:
            raise ValidationError("رمز عبور و تکرار آن یکسان نمی باشد.")
        return pass_2
    
    def save(self, commit = True):
        user = super().save(commit=False)
        user.user_type = "user"
        user.set_password(self.cleaned_data["password"])
        if user.first_name and user.last_name:
            user.username = f"{user.first_name.lower()}_{user.last_name.lower()}"
        else:
            user.username = f"default_username{code_generator(5)}"
        if commit:
            user.save()
        return user

 
#=============================================================================================