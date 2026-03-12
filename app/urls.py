
from app import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.urls import path


app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('regist/', views.regist, name='regist'),
    path('activate_user/<uuid:token>/',views.activate_user, name='activate_user'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('edit/', views.user_edit, name='profile_edit'),
    path('email/change/', views.email_change, name='email_change'),
    path("password_reset/",auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="registration/password_reset_email.html",
    ),name="password_reset",
),
    path("password_reset/done/",
    auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ),name="password_reset_done",
),
    path("password-reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
    ),
    name="password_reset_confirm",
),
    path("password-reset-complete/",views.password_reset_complete_redirect,
    name="password_reset_complete",
),
    path(
    "password_change/",
    auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change.html",
        success_url=reverse_lazy("accounts:password_change_done"),
    ),
    name="password_change",
),

    path(
    "password_change/done/",
    auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html",
    ),
    name="password_change_done",
),

   path('stamp/<int:goal_id>/',views.stamp_select, name="stamp_select"),
   path('calendar/', views.calendar_redirect, name='calendar'),
   path('calendar/<int:year>/<int:month>/', views.calendar_view, name="calendar_view"),
   path('not_achieved/<int:goal_id>', views.not_achieved, name="not_achieved"),
   path('mypage/', views.mypage, name='mypage'),
   path('goal/add/', views.goal_create, name='goal_create'),
   #フッターの「記録」↓
   path('record/', views.record_top, name="record_top"),
   #「目標」を押したら行く記録画面↓
   path("study/<int:goal_id>/", views.study_record, name="study_record"),
   path('icon/change/', views.icon_change, name="icon_change"),
  ]
