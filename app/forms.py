from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profile
from .models import Goal
from datetime import date

User = get_user_model()

class RegistForm(forms.ModelForm):
    birthday = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    password = forms.CharField(
         label="パスワード(英大文字・数字を含む８文字以上)",
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
                   for error in e:
                       self.add_error('password', error)
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

class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="現在のパスワード",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
        )
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
        )
    new_password2 = forms.CharField(
        label="新しいパスワード（確認用）",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
        )

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

HOUR_CHOICES = [(i, f"{i}") for i in range(0, 13)]         # 0〜12時間
MIN_CHOICES  = [(i, f"{i:02d}") for i in range(0, 60, 5)]  # 0,5,10...55分

PAGE_CHOICES = [(i, f"{i}") for i in range(0, 501)]        # 0〜500ページ（好きに変えてOK）

class GoalForm(forms.ModelForm):
    study_hour = forms.ChoiceField(choices=HOUR_CHOICES, label="勉強時間（時）")
    study_minute = forms.ChoiceField(choices=MIN_CHOICES, label="勉強時間（分）")
    page_start = forms.ChoiceField(choices=PAGE_CHOICES, label="開始ページ")
    page_end = forms.ChoiceField(choices=PAGE_CHOICES, label="終了ページ")

    class Meta:
        model = Goal
        fields = ['date', 'subject', 'study_hour', 'study_minute', 'page_start', 'page_end']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date',
                                           'class': 'form-input',})
        }



    def clean_date(self):
        goal_date = self.cleaned_data.get("date")
        if goal_date and goal_date > date.today():
            raise forms.ValidationError("未来の日付は選べません。今日までの日付を選んでください。")

        return goal_date

    def clean(self):
        cleaned = super().clean()

        # ChoiceFieldは文字列で来るので int に変換して、ついでに整合性チェック
        try:
            s = int(cleaned.get("page_start") or 0)
            e = int(cleaned.get("page_end") or 0)
        except ValueError:
            return cleaned

        if e < s:
            self.add_error("page_end", "終了ページは開始ページ以上にしてください。")

        return cleaned