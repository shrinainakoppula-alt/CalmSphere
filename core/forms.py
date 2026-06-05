from django import forms
from django.contrib.auth.models import User
from core.models import UserProfile
import re

class RegistrationForm(forms.Form):
    fullname = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'required': 'required'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'required': 'required'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address', 'required': 'required'})
    )
    mobile = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Mobile Number', 'required': 'required'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'required': 'required'})
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'required': 'required'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email address is already registered.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile').strip()
        mobile_digits = re.sub(r'\D', '', mobile)
        if len(mobile_digits) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        if UserProfile.objects.filter(mobile=mobile_digits).exists():
            raise forms.ValidationError("Mobile number is already registered.")
        return mobile_digits

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'required': 'required'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'required': 'required'})
    )
