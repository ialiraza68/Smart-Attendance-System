from django.contrib import admin

from .models import (
    AcademicSession,
    Program,
    AcademicClass,
    Section,
    Student,
    Subject,
    ClassSubject,
    Teacher,
    TeachingAssignment,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'start_date',
        'end_date',
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
    )

    ordering = (
        '-start_date',
    )


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
    )

    ordering = (
        'name',
    )


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = (
        'program',
        'year',
        'session',
        'is_active',
    )

    list_filter = (
        'session',
        'program',
        'year',
        'is_active',
    )

    search_fields = (
        'program__name',
        'session__name',
    )

    autocomplete_fields = (
        'session',
        'program',
    )

    ordering = (
        'program',
        'year',
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'class_obj',
        'capacity',
        'is_active',
    )

    list_filter = (
        'is_active',
        'class_obj__program',
        'class_obj__session',
    )

    search_fields = (
        'name',
        'class_obj__program__name',
        'class_obj__session__name',
    )

    autocomplete_fields = (
        'class_obj',
    )

    ordering = (
        'class_obj',
        'name',
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'roll_number',
        'name',
        'father_name',
        'section',
        'gender',
        'parent_phone',
        'status',
        'admission_date',
    )

    list_filter = (
        'status',
        'gender',
        'section__class_obj__program',
        'section__class_obj__session',
    )

    search_fields = (
        'roll_number',
        'registration_number',
        'name',
        'father_name',
        'phone',
        'parent_phone',
    )

    autocomplete_fields = (
        'section',
    )

    ordering = (
        'roll_number',
    )

    fieldsets = (
        ('Student Information', {
            'fields': (
                'roll_number',
                'registration_number',
                'name',
                'father_name',
                'gender',
                'date_of_birth',
                'image',
            )
        }),

        ('Contact Information', {
            'fields': (
                'phone',
                'parent_phone',
                'email',
                'address',
            )
        }),

        ('Academic Information', {
            'fields': (
                'section',
                'admission_date',
                'status',
            )
        }),

        ('Additional Information', {
            'fields': (
                'remarks',
            )
        }),
    )

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'code',
    )

    ordering = (
        'name',
    )


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = (
        'academic_class',
        'subject',
        'is_active',
    )

    list_filter = (
        'is_active',
        'academic_class__program',
        'academic_class__session',
        'subject',
    )

    search_fields = (
        'academic_class__program__name',
        'academic_class__session__name',
        'subject__name',
        'subject__code',
    )

    autocomplete_fields = (
        'academic_class',
        'subject',
    )

    ordering = (
        'academic_class',
        'subject',
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'get_name',
        'get_username',
        'qualification',
        'phone',
        'is_active',
    )

    list_filter = (
        'is_active',
        'user__role',
    )

    search_fields = (
        'employee_id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone',
    )

    autocomplete_fields = (
        'user',
    )

    ordering = (
        'employee_id',
    )

    @admin.display(
        description='Name',
        ordering='user__first_name'
    )
    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(
        description='Username'
    )
    def get_username(self, obj):
        return obj.user.username


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'teacher',
        'get_subject',
        'section',
        'get_class',
        'is_active',
    )

    list_filter = (
        'is_active',
        'section__class_obj__program',
        'section__class_obj__session',
        'class_subject__subject',
        'teacher',
    )

    search_fields = (
        'teacher__employee_id',
        'teacher__user__username',
        'teacher__user__first_name',
        'teacher__user__last_name',
        'class_subject__subject__name',
        'class_subject__subject__code',
        'section__name',
    )

    autocomplete_fields = (
        'teacher',
        'class_subject',
        'section',
    )

    ordering = (
        'teacher',
        'section',
    )

    @admin.display(description='Subject')
    def get_subject(self, obj):
        return obj.class_subject.subject.name

    @admin.display(description='Class')
    def get_class(self, obj):
        return obj.section.class_obj