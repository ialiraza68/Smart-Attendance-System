from django.db import models

# Create your models here.
class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Program(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class AcademicClass(models.Model):
    YEAR_CHOICES = (
        ('1ST', '1st Year'),
        ('2ND', '2nd Year'),
    )

    session = models.ForeignKey(
        AcademicSession,
        on_delete=models.CASCADE,
        related_name='classes'
    )

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='classes'
    )

    year = models.CharField(
        max_length=10,
        choices=YEAR_CHOICES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'program', 'year']
        ordering = ['program', 'year']

    def __str__(self):
        return f"{self.program.name} - {self.get_year_display()} ({self.session.name})"

class Section(models.Model):
    class_obj = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    name = models.CharField(max_length=10)

    capacity = models.PositiveIntegerField(
        default=50
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['class_obj', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.class_obj} - Section {self.name}"

class Student(models.Model):
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('LEFT', 'Left'),
        ('GRADUATED', 'Graduated'),
    )

    roll_number = models.CharField(
        max_length=50,
        unique=True
    )

    registration_number = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    name = models.CharField(max_length=200)

    father_name = models.CharField(max_length=200)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    parent_phone = models.CharField(
        max_length=15
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='students'
    )

    admission_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    image = models.ImageField(
        upload_to='students/',
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['roll_number']

    def __str__(self):
        return f"{self.roll_number} - {self.name}"

class Subject(models.Model):
    name = models.CharField(
        max_length=100
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class ClassSubject(models.Model):
    academic_class = models.ForeignKey(
        AcademicClass,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='class_subjects'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['academic_class', 'subject'],
                name='unique_class_subject'
            )
        ]

        ordering = ['academic_class', 'subject']

    def __str__(self):
        return f"{self.academic_class} - {self.subject.name}"

from django.conf import settings
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )

    employee_id = models.CharField(
        max_length=50,
        unique=True
    )

    qualification = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    joining_date = models.DateField(
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

class TeachingAssignment(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )

    class_subject = models.ForeignKey(
        ClassSubject,
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )

    is_active = models.BooleanField(
        default=True
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'class_subject', 'section'],
                name='unique_teaching_assignment'
            )
        ]

        ordering = ['teacher', 'section']

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.class_subject.subject.name} - "
            f"{self.section}"
        )

class StudentAttendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='legacy_attendance_records'
    )

    teaching_assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PRESENT'
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'student',
                    'teaching_assignment',
                    'date'
                ],
                name='unique_student_assignment_date'
            )
        ]

        ordering = ['-date', 'student']

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.teaching_assignment.class_subject.subject.name} - "
            f"{self.date} - "
            f"{self.get_status_display()}"
        )

class AttendanceSession(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('LOCKED', 'Locked'),
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='attendance_sessions'
    )

    date = models.DateField()

    taken_by = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='attendance_sessions'
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'section']
        constraints = [
            models.UniqueConstraint(
                fields=['section', 'date'],
                name='unique_section_attendance_per_day'
            ),
        ]

    def __str__(self):
        return f"{self.section} - {self.date}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'Leave'),
    )

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='attendance_records'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name='marked_attendance_records'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__roll_number']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'student'],
                name='unique_student_per_attendance_session'
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.roll_number} - "
            f"{self.session.date} - "
            f"{self.get_status_display()}"
        )


class AttendanceCorrection(models.Model):
    record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.PROTECT,
        related_name='corrections',
    )
    previous_status = models.CharField(max_length=10, choices=AttendanceRecord.STATUS_CHOICES)
    new_status = models.CharField(max_length=10, choices=AttendanceRecord.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='attendance_corrections',
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.record} corrected by {self.changed_by}"