from django.contrib.auth.decorators import login_required
from . import forms
from uuid import uuid4
from django.shortcuts import render, redirect, get_object_or_404,redirect,render
from . forms import RegistForm
from . models import UserActivateToken
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from datetime import date
from collections import defaultdict
import calendar as pycalendar
from .models import Profile, Goal, StudyRecord, CustomUser
from .forms import ProfileForm
from .forms import GoalForm
from django.db.models import Exists, OuterRef
from django.conf import settings
from .forms import ProfileIconForm
from django.http import HttpResponse
from django.utils.dateparse import parse_date


@login_required
def home(request):
    q = request.GET.get("date")
    selected_date = parse_date(q) if q else date.today()

    if selected_date is None:
        selected_date = date.today()

    goals = Goal.objects.filter(
        user=request.user,
        date=selected_date
        ).order_by("id")

    profile, _ = Profile.objects.get_or_create(user=request.user)

    has_goals = Goal.objects.filter(user=request.user).exists()

    return render(request, "accounts/home.html",{
        "profile": profile,
        "goals": goals,
        "selected_date": selected_date,
        "has_goals": has_goals,
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
    if request.user.is_authenticated:
        return redirect('accounts:home')
    login_form = LoginForm(request.POST or None)
    if login_form.is_valid():
        email = login_form.cleaned_data['email']
        password = login_form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)
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
    profile, _ = Profile.objects.get_or_create(user=request.user)

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

        if not profile.name:
            profile.name = request.user.username or request.user.email
        if not profile.birthday:
            profile.birthday = request.user.birthday
        profile.save()

        form = ProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html',{
            'form': form,
            'profile': profile,
            })


def email_change(request):
    if request.method == "POST":
        new_email = request.POST.get("email", "").strip().lower()
        current_email = (request.user.email or "").strip().lower()

        if not new_email:
            return render(request, "accounts/email_change.html", {
                "error_message": "メールアドレスを入力してください。",
                "entered_email": new_email,
            })

        if new_email == current_email:
            return render(request, "accounts/email_change.html", {
                "error_message": "現在と同じメールアドレスです。",
                "entered_email": new_email,
            })

        request.user.email = new_email
        request.user.save()

        return redirect("accounts:mypage")

    return render(request, "accounts/email_change.html")

@login_required

def icon_change(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        icon_file = request.FILES.get("icon_gallery") or request.FILES.get("icon_camera")

        if icon_file:
            profile.icon = icon_file
            profile.save()
            return redirect("accounts:profile_edit")
        return render(request, "accounts/icon_change.html", {
            "profile": profile,
            "error": "画像を選択してください",
        })
    return render(request, "accounts/icon_change.html",{
        "profile": profile,
    })

@login_required
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

@login_required
def study_record(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    today = timezone.localdate()

    q = request.GET.get("date")
    selected_date = parse_date(q) if q else timezone.localdate()
    if selected_date is None:
        selected_date = timezone.localdate()

    if selected_date > today:
       messages.error(request, "未来の日付では記録できません。")
       return redirect("accounts:study_record",goal_id=goal.id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "achieved":
            return redirect(f"/accounts/stamp/{goal.id}/?date={selected_date.strftime('%Y-%m-%d')}")

    return render(request,
        "accounts/study_record.html",
        {
            'goal': goal,
            'selected_date': selected_date,
            'today': today,
        }
    )

@login_required
def stamp_select(request, goal_id):
    goal = get_object_or_404(
        Goal,
        id=goal_id,
        user=request.user,
    )

    today = timezone.localdate()

    q = request.GET.get("date")
    target_date = parse_date(q) if q else None
    if target_date is None:
        target_date = today

    if target_date > today:
        messages.error(request, "未来の日付ではスタンプを記録できません。")
        return redirect("accounts:stamp_select",goal_id=goal.id)

    if request.method == "POST":

        shape = request.POST.get("shape")
        color = request.POST.get("color")

        q_post = request.POST.get("date")
        target_date_post = parse_date(q_post) if q_post else None

        if target_date_post is None:
            messages.error(request, "日付が不正です。")
            return redirect("accounts:calendar_view", year=date.today().year, month=date.today().month)

        if not (shape and color):
            messages.error(request, "スタンプを選んでください。")
            return redirect("accounts:calendar_view", year=target_date_post.year, month=target_date_post.month)

        StudyRecord.objects.update_or_create(
            user=request.user,
            goal=goal,
            defaults={
                "subject": goal.subject,
                "date": target_date_post,
                "achieved": True,
                "result": "achieved",
                "stamp_shape": shape,
                "stamp_color": color,
            }
        )

        return redirect(
            "accounts:calendar_view",
            year=target_date_post.year,
            month=target_date_post.month)

    return render(request, "accounts/stamp_select.html", {
        "goal": goal,
        "target_date": target_date,
    })
@login_required
def calendar_view(request, year, month):

    today = timezone.localdate()

    month_goals = Goal.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month,
    ).order_by("date", "id")

    goals_dict = defaultdict(list)
    for g in month_goals:
        goals_dict[g.date].append(g)


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

    for day, recs in stamp_dict.items():
        stamped = [r for r in recs if r.stamp_shape]
        not_stamped = [r for r in recs if not r.stamp_shape]
        stamp_dict[day] =stamped + not_stamped

    stamp_count_dict ={}
    for day, recs in stamp_dict.items():
        stamped_count = len([r for r in recs if r.stamp_shape])
        stamp_count_dict[day] = stamped_count

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
            "stamp_count_dict": stamp_count_dict,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "today": today,



    })

@login_required

def calendar_redirect(request):
    today = date.today()
    return redirect(
        'accounts:calendar_view',
        year=today.year,
        month=today.month
    )
def not_achieved(request):
    today = date.today()
    year = today.year
    month = today.month
    return render(request,'accounts/not_achieved.html',{
       "year": year,
       "month": month, })

@login_required

def record_create(request, goal_id):
    return render(request, 'accounts/record_form.html',{
        'goal_id': goal_id
    })

@login_required
def record_top(request):

    recorded_goals = StudyRecord.objects.filter(
        user=request.user
    ).values_list("goal_id", flat=True)


    goals = (
        Goal.objects
        .filter(user=request.user)
        .exclude(id__in=recorded_goals)
    )
    return render(
        request,
        "accounts/record_top.html",
        {"goals": goals}
    )

@login_required
def goal_create(request):
    q = request.GET.get("date")
    initial_date = parse_date(q) if q else None

    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            goal_date = form.cleaned_data["date"]

            same_day_count = Goal.objects.filter(
                user=request.user,
                date=goal_date
            ).count()

            if same_day_count >= 6:
                messages.error(request, "目標は同じ日に6個までです。")
                return redirect(f"/accounts/goal/add/?date={goal_date.strftime('%Y-%m-%d')}")

            subject = form.cleaned_data["subject"]
            study_hour = form.cleaned_data["study_hour"]
            study_minute = form.cleaned_data["study_minute"]
            page_start = form.cleaned_data["page_start"]
            page_end = form.cleaned_data["page_end"]

            if Goal.objects.filter(
                user=request.user,
                date=goal_date,
                subject=subject,
                study_hour=study_hour,
                study_minute=study_minute,
                page_start=page_start,
                page_end=page_end,).exists():
                    form.add_error(None, "同じ目標はすでに登録されています。")
            else:
                goal = form.save(commit=False)
                goal.user = request.user
                goal.save()
                return redirect("accounts:home")
    else:
        form = GoalForm(initial={"date": initial_date} if initial_date else None)

    day_goals_count = Goal.objects.filter(
        user=request.user,
        date=initial_date
    ).count() if initial_date else 0

    return render(request, "accounts/goal_form.html", {
        "form": form,
        "day_goals_count": day_goals_count,
        "initial_date": initial_date,
    })


@login_required
def not_achieved(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    today = timezone.localdate()

    q = request.GET.get("date")
    target_date = parse_date(q) if q else goal.date

    if target_date and target_date > today:
        messages.error(request, "未来の日付では記録できません。")
        return redirect("accounts:study_record", goal_id=goal.id)

    StudyRecord.objects.update_or_create(
        user=request.user,
        goal=goal,
        defaults={
            "subject": goal.subject,
            "date": target_date,
            "result": "not_achieved",
            "achieved": False,
        }
    )

    return render(request, "accounts/not_achieved.html", {
        "goal": goal,
        "target_date": target_date,
    })

def portfolio(request):
    return render(request, 'portfolio/work-01.html')

def index(request):
    return HttpResponse('templates/index.html')