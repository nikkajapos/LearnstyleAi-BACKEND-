from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    learning_style = models.CharField(max_length=20, blank=True, null=True)
    match_percentage = models.IntegerField(default=0)
    last_score = models.IntegerField(default=0)
    assessment_date = models.DateField(blank=True, null=True)
    streak = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    course_completion = models.IntegerField(default=0)
    vark_visual = models.IntegerField(default=0)
    vark_auditory = models.IntegerField(default=0)
    vark_readwrite = models.IntegerField(default=0)
    vark_kinesthetic = models.IntegerField(default=0)
    section = models.CharField(max_length=100, blank=True, null=True)
    instructor = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='students', limit_choices_to={'role': 'instructor'}
    )
    is_active_account = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class AssessmentResult(models.Model): 
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_history')
    learning_style = models.CharField(max_length=20)
    match_percentage = models.IntegerField()
    score = models.IntegerField()
    vark_visual = models.IntegerField(default=0)
    vark_auditory = models.IntegerField(default=0)
    vark_readwrite = models.IntegerField(default=0)
    vark_kinesthetic = models.IntegerField(default=0)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']

    def __str__(self):
        return f"{self.student.username} - {self.learning_style} ({self.taken_at.date()})"
