from . import forms
from uuid import uuid4
from django.shortcuts import render, redirect, get_object_or_404
from . forms import RegistForm
from . models import UserActivateToken
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import StudyRecord
from datetime import date
from collections import defaultdict
import calendar as pycalendar
from .models import Profile, Goal
from .forms import ProfileForm
from .forms import GoalForm
from .models import Goal
from django.db.models import Exists, OuterRef
from django.conf import settings
from .forms import ProfileIconForm

@login_required
def home(request):
    profile = None
    user = request.user

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        goals = Goal.objects.filter(
            user=request.user,
            date=date.today()
            )

    print("ログイン中ユーザー:", user)
    print("取得したプロフィール:", profile)
    

    return render(request, "accounts/home.html",{
        "profile": profile,
        "goals": goals,
    })
def regist(request):
    if request.method == "POST":
        form = RegistForm(request.POST)
        if form.is_valid():
           user = form.save()
           token= uuid4()
           expired_at=timezone.now() + timedelta(days=1)

           UserActivateToken.objects.update_or_create(
                user=user,
                defaults={
                  'token': token,
                  'expired_at': expired_at,
                }
            )
           login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
           return redirect('accounts:home')
        return render(request,'accounts/regist.html', {'regist_form': form,})
    form = RegistForm()
    return render(request, "accounts/regist.html", {"regist_form": form})
def activate_user(request, token):
    activate_form = forms.UserActivateForm(request.POST or None)
    if activate_form.is_valid():
        UserActivateToken.objects.activate_user_by_token(token) #ユーザー有効化
        messages.success(request, '登録しました')
    activate_form.initial['token'] = token
    return render(
        request, 'accounts/activate_user.html', context={
            'activate_form': activate_form,
        }
    )
def user_login(request):
    login_form = LoginForm(request.POST or None)
    if login_form.is_valid():
        email = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('accounts:home')
        else:
            messages.error(request, 'ログインに失敗しました')
    return render(
        request, 'accounts/user_login.html', context={
            'login_form': login_form,
        }
    )

@login_required
def user_logout(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def user_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method =='POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )
        if form.is_valid():
           form.save()
           return redirect('accounts:mypage')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/profile_edit.html',{
            'form': form,
            'profile': profile,
            })


def email_change(request):
    if request.method == "POST":
        new_email = request.POST.get("email")
        request.user.email = new_email
        request.user.save()

        return redirect('accounts:mypage')
    return render(request, 'accounts/email_change.html')

def icon_change(request):
    profile = request.user.profile  

    if request.method == "POST":
        file_obj = request.FILES.get("icon_gallery") or request.FILES.get("icon_camera")

        if file_obj:
            profile.icon = file_obj
            profile.save()
            return redirect("accounts:profile_edit")
        return render(request, "accounts/icon_change.html", {
            "profile": profile,
            "error": "画像を選択してください",
        })
    return render(request, "accounts/icon_change.html",{
        "profile": profile,
    })

def mypage(request):
    profile = Profile.objects.filter(user=request.user).first()
    return render(request, 'accounts/mypage.html', {
        'profile': profile
    })

@login_required
def password_reset(request):
    password_reset_form = forms.PasswordResetForm(
        request.POST or None, instance=request.user
        )
    if password_reset_form.is_valid():
        password_reset_form.save(commit=True)
        messages.success(request,'パスワードを更新しました')

    return render(
        request,'accounts/reset_password.html', context={
            'password_reset_form': password_reset_form,
        }
    )

def password_reset_complete_redirect(request):
    return redirect("accounts:login")

def study_record(request, goal_id):
    today = timezone.localdate()
    goal = get_object_or_404(Goal, id=goal_id)
    
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "achieved":
            return redirect(
                "accounts:stamp_select",
                goal_id=goal.id,
            )

    return render(request,
        "accounts/study_record.html",
        {
            'goal': goal,
            'date': today,
        }
    )

def stamp_select(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == "POST":
        shape = request.POST.get("shape")
        color = request.POST.get("color")
        
        StudyRecord.objects.create(
            user=request.user,
            subject=goal.subject,
            date=date.today(),
            achieved=True,
            stamp_shape=shape,
            stamp_color=color,

        )
        today = date.today()
        return redirect('accounts:calendar',year=today.year, month=today.month)
    return render(request, "accounts/stamp_select.html",{
        "goal": goal
        })
def calendar(request):
    records = StudyRecord.objects.filter(
        user=request.user
    )
    return render(
        request,
        "accounts/calendar.html",
        { records: records
        }
    )
def calendar_view(request, year, month):
    today = date.today()

    cal = pycalendar.Calendar(firstweekday=6)
    month_days= cal.monthdatescalendar(year, month)

    records = StudyRecord.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month,
    )
    stamp_dict = defaultdict(list)
    for r in records:
        stamp_dict[r.date].append(r)

    prev_month = month -1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -=1
    next_month = month + 1
    next_year = year
    if next_month ==13:
        next_month = 1
        next_year += 1

    return render(
        request,
        "accounts/calendar.html",
        {
            "year": year,
            "month": month,
            "month_days": month_days,
            "stamp_dict": dict(stamp_dict),
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "today": today,
            "month_days": month_days,
            
   
    })

def not_achieved(request):
    today = date.today()
    year = today.year
    month = today.month
    return render(request,'accounts/not_achieved.html',{ 
       "year": year,
       "month": month, })

def goal_create(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('accounts:home')
    else:
        form = GoalForm()

    return render(request, 'accounts/goal_form.html', {
        'form': form
    })
def record_create(request, goal_id):
    return render(request, 'accounts/record_form.html',{
        'goal_id': goal_id
    })
def record_top(request):
    recorded_subjects = StudyRecord.objects.filter(
        user=request.user
    ).values_list("subject", flat=True)
    goals = Goal.objects.filter(
        user=request.user
    ).exclude(subject__in=recorded_subjects)
    return render(
        request,
        "accounts/record_top.html",
        {"goals": goals}
    )