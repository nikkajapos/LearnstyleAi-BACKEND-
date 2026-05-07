from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Avg
from .models import AssessmentResult
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    UserAdminSerializer,
    AssessmentResultSerializer,
    InstructorStudentSerializer,
)

User = get_user_model()


# ─── Auth ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """POST /api/auth/register/"""
    name = request.data.get('name', '').strip()
    parts = name.split(' ', 1)

    data = request.data.copy()
    data['username'] = request.data.get('email', '')
    data['first_name'] = parts[0] if parts else ''
    data['last_name'] = parts[1] if len(parts) > 1 else ''

    serializer = RegisterSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """POST /api/auth/login/"""
    from django.contrib.auth import authenticate

    email = request.data.get('email', '')
    password = request.data.get('password', '')

    user = authenticate(request, username=email, password=password)
    if user is None:
        try:
            u = User.objects.get(email=email)
            user = authenticate(request, username=u.username, password=password)
        except User.DoesNotExist:
            pass

    if user is None:
        return Response(
            {'detail': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserProfileSerializer(user).data,
    })


# ─── Profile ─────────────────────────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
def profile(request):
    """GET/PATCH /api/profile/"""
    if request.method == 'GET':
        return Response(UserProfileSerializer(request.user).data)

    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── Assessment ───────────────────────────────────────────────────────────────

@api_view(['POST'])
def submit_assessment(request):
    """POST /api/assessment/submit/"""
    user = request.user
    if user.role != 'student':
        return Response(
            {'detail': 'Only students can submit assessments.'},
            status=status.HTTP_403_FORBIDDEN
        )

    data = request.data
    learning_style = data.get('learningStyle')
    match_percentage = data.get('matchPercentage', 0)
    score = data.get('score', 0)
    vark = data.get('varkScores', {})

    result = AssessmentResult.objects.create(
        student=user,
        learning_style=learning_style,
        match_percentage=match_percentage,
        score=score,
        vark_visual=vark.get('Visual', 0),
        vark_auditory=vark.get('Auditory', 0),
        vark_readwrite=vark.get('Read/Write', 0),
        vark_kinesthetic=vark.get('Kinesthetic', 0),
    )

    user.learning_style = learning_style
    user.match_percentage = match_percentage
    user.last_score = score
    user.assessment_date = result.taken_at.date()
    user.vark_visual = vark.get('Visual', 0)
    user.vark_auditory = vark.get('Auditory', 0)
    user.vark_readwrite = vark.get('Read/Write', 0)
    user.vark_kinesthetic = vark.get('Kinesthetic', 0)
    user.save()

    return Response(UserProfileSerializer(user).data)


@api_view(['GET'])
def assessment_history(request):
    """GET /api/assessment/history/"""
    results = AssessmentResult.objects.filter(student=request.user)
    return Response(AssessmentResultSerializer(results, many=True).data)


class AssessmentResultListCreateView(generics.ListCreateAPIView):
    serializer_class = AssessmentResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssessmentResult.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


class AssessmentResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssessmentResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssessmentResult.objects.filter(student=self.request.user)


# ─── Student Dashboard ────────────────────────────────────────────────────────

@api_view(['GET'])
def student_dashboard(request):
    """GET /api/student/dashboard/"""
    user = request.user
    if user.role != 'student':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    from django.utils import timezone
    from datetime import timedelta

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    today = timezone.now().date()
    start = today - timedelta(days=today.weekday())

    weekly = []
    for i, day in enumerate(days):
        d = start + timedelta(days=i)
        count = AssessmentResult.objects.filter(student=user, taken_at__date=d).count()
        weekly.append({'day': day, 'assessments': count})

    return Response({
        'profile': UserProfileSerializer(user).data,
        'weeklyActivity': weekly,
    })


# ─── Instructor Dashboard ─────────────────────────────────────────────────────

@api_view(['GET'])
def instructor_dashboard(request):
    """GET /api/instructor/dashboard/"""
    user = request.user
    if user.role != 'instructor':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    students = User.objects.filter(instructor=user, role='student')
    student_data = InstructorStudentSerializer(students, many=True).data

    style_counts = {}
    for s in students:
        style = s.learning_style or 'Unknown'
        style_counts[style] = style_counts.get(style, 0) + 1
    distribution = [{'name': k, 'value': v} for k, v in style_counts.items()]

    from django.utils import timezone
    from datetime import timedelta

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    today = timezone.now().date()
    start = today - timedelta(days=today.weekday())

    weekly = []
    for i, day in enumerate(days):
        d = start + timedelta(days=i)
        count = AssessmentResult.objects.filter(student__instructor=user, taken_at__date=d).count()
        weekly.append({'day': day, 'assessments': count})

    avg_score = students.aggregate(avg=Avg('last_score'))['avg'] or 0

    return Response({
        'studentCount': students.count(),
        'avgScore': round(avg_score, 1),
        'students': student_data,
        'classDistribution': distribution,
        'weeklyActivity': weekly,
    })


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@api_view(['GET'])
def admin_dashboard(request):
    """GET /api/admin/dashboard/"""
    if request.user.role != 'admin':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all()

    from django.utils import timezone
    from datetime import timedelta

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    today = timezone.now().date()
    start = today - timedelta(days=today.weekday())

    weekly = []
    for i, day in enumerate(days):
        d = start + timedelta(days=i)
        logins = User.objects.filter(last_login__date=d).count()
        assessments = AssessmentResult.objects.filter(taken_at__date=d).count()
        weekly.append({'day': day, 'logins': logins, 'assessments': assessments})

    return Response({
        'users': UserAdminSerializer(users, many=True).data,
        'totalAssessments': AssessmentResult.objects.count(),
        'weeklySystemActivity': weekly,
    })


@api_view(['PATCH'])
def admin_update_user(request, user_id):
    """PATCH /api/admin/users/<id>/"""
    if request.user.role != 'admin':
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    allowed = ['role', 'is_active_account', 'section']
    for field in allowed:
        if field in request.data:
            setattr(target, field, request.data[field])

    instructor_id = request.data.get('instructorId')
    if instructor_id is not None:
        try:
            instructor = User.objects.get(pk=instructor_id, role='instructor')
            target.instructor = instructor
            target.section = instructor.section or target.section
        except User.DoesNotExist:
            pass

    target.save()
    return Response(UserAdminSerializer(target).data)