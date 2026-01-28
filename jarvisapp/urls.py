from django.contrib import admin
from django.urls import path
from core.views import (
    LoginView,
    AdminCreateUserView,
    AdminCreateTaskView,
    AdminNotificationView,
    AdminActivityView,
    UserTaskView,
    CompleteTaskView,
    UserNotificationView,
    AppOpenView,
    AdminUserListView,
    LogoutView,
    AgentChatView,
    AgentResultView,
    ClientLeadDetailView,
    ClientLeadListCreateView,
    AdminUpdateTaskView,
    AdminTaskListView,
    UserReportCreateListView,
   AdminReportListView,
    TodayTomorrowSpecialityView,
    AdminUpdateUserPasswordView,
    admin_login_view,
    admin_dashboard_view,
    admin_update_password_view,
    admin_delete_notification,
    admin_delete_report,
    admin_delete_client,

)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 Auth
    path('api/login/', LoginView.as_view()),
    
    path('admin-login/', admin_login_view, name='admin-login'),
    path('admin-dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('dashboard/update-password/', admin_update_password_view),

    path('dashboard/delete-notification/<int:id>/', admin_delete_notification),
    path('dashboard/delete-report/<int:id>/', admin_delete_report),
    path('dashboard/delete-client/<int:id>/', admin_delete_client),

    # 👨‍💼 Admin APIs
    path('api/admin/create-user/', AdminCreateUserView.as_view()),
    path('api/admin/create-task/', AdminCreateTaskView.as_view()),
    path('api/admin/notification/', AdminNotificationView.as_view()),
    path('api/admin/activity/', AdminActivityView.as_view()),
    path('api/admin/users/', AdminUserListView.as_view()),
    path("api/day-speciality/", TodayTomorrowSpecialityView.as_view()),
    path(
        "api/admin/users/update-password/",
        AdminUpdateUserPasswordView.as_view(),
        name="admin-update-user-password",
    ),

    # 👤 User APIs
    path('api/tasks/', UserTaskView.as_view()),
    path('api/tasks/<int:task_id>/complete/', CompleteTaskView.as_view()),
    path('api/notifications/', UserNotificationView.as_view()),
    path('api/app-open/', AppOpenView.as_view()),
    
    path("api/clients/", ClientLeadListCreateView.as_view()),
    path("clients/<int:pk>/", ClientLeadDetailView.as_view()),
    path(
        "api/admin/tasks/<int:task_id>/",
        AdminUpdateTaskView.as_view(),
        name="admin-update-task",
    ),
    path("api/admin/tasks/", AdminTaskListView.as_view()),
    
    path("api/reports/", UserReportCreateListView.as_view()),

    # 🧑‍💼 Admin Reports
    path("api/admin/reports/", AdminReportListView.as_view()),
    
     path("admin-login/", admin_login_view, name="admin-login"),

    
    
    #-----------logout---------
    
    path('api/logout/', LogoutView.as_view()),
    #--------AI---------
    path("api/agent/chat/", AgentChatView.as_view()),
    path("api/agent/result/<str:task_id>/", AgentResultView.as_view()),
    

]
