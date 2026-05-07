from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Assessment
    path('assessment/submit/', views.submit_assessment, name='assessment_submit'),
    path('assessment/history/', views.assessment_history, name='assessment_history'),
    path('assessment/results/', views.AssessmentResultListCreateView.as_view(), name='assessment_results'),
    path('assessment/results/<int:pk>/', views.AssessmentResultDetailView.as_view(), name='assessment_result_detail'),

    # Dashboards
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/<int:user_id>/', views.admin_update_user, name='admin_update_user'),
]
