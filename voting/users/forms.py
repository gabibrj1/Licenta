from django import forms
from .models import User

#formular pentru inregistrarea utilizatorilor
class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']

    def clean(self):
        #validare suplimentara pt a verifica daca parola si confirmarea parolei coincid
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Parolele nu se potrivesc")
        return cleaned_data

#formular pentru completarea datelor din carte de identitate
class IDCardForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['cnp', 'series', 'number', 'first_name', 'last_name', 
                  'place_of_birth', 'address', 'issuing_authority', 
                  'sex', 'date_of_issue', 'date_of_expiry']
