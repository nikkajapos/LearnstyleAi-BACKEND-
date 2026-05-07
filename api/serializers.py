from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AssessmentResult

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'name', 'role', 'password']

    def create(self, validated_data):
        name = validated_data.pop('name', '').strip()
        if name and not validated_data.get('first_name') and not validated_data.get('last_name'):
            parts = name.split(' ', 1)
            validated_data['first_name'] = parts[0]
            validated_data['last_name'] = parts[1] if len(parts) > 1 else ''

        if not validated_data.get('username'):
            validated_data['username'] = validated_data.get('email', '')

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    varkScores = serializers.SerializerMethodField()
    assessmentHistory = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'role',
            'first_name', 'last_name',
            'learning_style', 'match_percentage', 'last_score', 'assessment_date',
            'streak', 'lessons_completed', 'course_completion',
            'varkScores', 'assessmentHistory', 'section', 'is_active_account',
        ]
        read_only_fields = ['id', 'email', 'role', 'varkScores', 'assessmentHistory', 'name']

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.username

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['name'] = self.get_name(instance)
        return data

    def update(self, instance, validated_data):
        name = self.initial_data.get('name')
        if isinstance(name, str):
            full = name.strip()
            parts = full.split(' ', 1) if full else ['', '']
            validated_data['first_name'] = parts[0]
            validated_data['last_name'] = parts[1] if len(parts) > 1 else ''
        return super().update(instance, validated_data)

    def get_varkScores(self, obj):
        return {
            'Visual': obj.vark_visual,
            'Auditory': obj.vark_auditory,
            'Read/Write': obj.vark_readwrite,
            'Kinesthetic': obj.vark_kinesthetic,
        }

    def get_assessmentHistory(self, obj):
        return [
            {
                'date': str(r.taken_at.date()),
                'style': r.learning_style,
                'score': r.score,
            }
            for r in obj.assessment_history.all()
        ]


class UserAdminSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    instructor_id = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'section', 'instructor_id', 'is_active_account']

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.username


class AssessmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentResult
        fields = ['id', 'learning_style', 'match_percentage', 'score',
                  'vark_visual', 'vark_auditory', 'vark_readwrite', 'vark_kinesthetic', 'taken_at']
        read_only_fields = ['id', 'taken_at']


class InstructorStudentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    style = serializers.CharField(source='learning_style')
    assessmentDate = serializers.DateField(source='assessment_date')

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'style', 'assessmentDate', 'last_score', 'section']

    def get_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.username
