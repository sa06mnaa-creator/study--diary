from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile
from .models import Goal

User = get_user_model()

class RegistForm(forms.ModelForm):
    birthday = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    password = forms.CharField(
         label="パスワード(英大文字数字・数字を含む８文字以上)",
         widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label='パスワード再入力',widget=forms.PasswordInput()
    )
    
    class Meta():
        model = User
        fields = ('username','birthday','email','password','confirm_password')
        labels ={
            'username': '名前',
            'birthday': '生年月日',
            'email': 'メールアドレス',
            'password': 'パスワード',
        }
        widgets = {
            'password': forms.PasswordInput() 
            }
    def clean(self):
            cleaned_data = super().clean()
            password = cleaned_data.get('password')            
            confirm_password = cleaned_data.get('confirm_password')
            if password and confirm_password and password != confirm_password:
                self.add_error('confirm_password','パスワードが一致しません')
            if password:
                try:
                    validate_password(password, self.instance)
                except ValidationError as e:
                  self.add_error('password', e)
            return cleaned_data
    def save(self, commit=True):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data['password'])
            if commit:
                user.save()
            return user
    
    class UserActivateForm(forms.Form):
         token = forms.CharField(widget=forms.HiddenInput())
class LoginForm(forms.Form):
         email = forms.EmailField(label="メールアドレス")
         password = forms.CharField(label="パスワード", widget=forms.PasswordInput())

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('icon','name','birthday','goal')
        widgets = {
               'birthday': forms.DateInput(attrs={'type': 'date'}),
               'goal': forms.Textarea(attrs={
                    'rows': 2,
                    'max_length': 20,
                    'placeholder': '20文字以内'
               }),
        
          }

class ProfileIconForm(forms.ModelForm):
     class Meta:
          model = Profile
          fields = ['icon']
          
class PasswordResetForm(forms.ModelForm):
    confirm_password = forms.CharField(label='パスワード再設定',widget=forms.PasswordInput())
    class Meta:
          model = User
          fields = ('password',)
          labels = {
               'password':'パスワード',
          }
          widgets = {
               'password': forms.PasswordInput()
          }
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data['password']
        confirm_password = cleaned_data['confirm_password']
        if password != confirm_password:
            self.add_error('password','パスワードが一致しません')
        try:
             validate_password(password, self.instance)
        except ValidationError as e:
             self.add_error('password', e)
             return cleaned_data
        def save(self, commit=False):
            user = super().save(commit=False)
            user.set_password(self.cleaned_data['password'])
            if commit:
                  user.save()
            return user
class GoalForm(forms.ModelForm):
     class Meta:
          model = Goal
          fields = [
               'date',
               'subject',
               'study_hour',
               'study_minute',
               'page_start',
               'page_end',
          ]
          widgets = {
               'date': forms.DateInput(
                    attrs={
                         'type': 'date'
                    }
               )
          }
