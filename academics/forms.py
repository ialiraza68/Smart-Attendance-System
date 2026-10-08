from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import (
    AcademicClass, AcademicSession, ClassSubject, Program, Section, Student,
    Subject, Teacher, TeachingAssignment,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"


class AcademicSessionForm(StyledModelForm):
    class Meta:
        model = AcademicSession
        fields = ("name", "start_date", "end_date", "is_active")
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("start_date") and cleaned.get("end_date") and cleaned["start_date"] >= cleaned["end_date"]:
            raise forms.ValidationError("The end date must be after the start date.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit)
        if commit and instance.is_active:
            AcademicSession.objects.filter(is_active=True).exclude(pk=instance.pk).update(is_active=False)
        return instance


class ProgramForm(StyledModelForm):
    class Meta:
        model = Program
        fields = ("name", "description", "is_active")


class AcademicClassForm(StyledModelForm):
    class Meta:
        model = AcademicClass
        fields = ("session", "program", "year", "is_active")


class SectionForm(StyledModelForm):
    class Meta:
        model = Section
        fields = ("class_obj", "name", "capacity", "is_active")

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return capacity


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = (
            "roll_number", "registration_number", "name", "father_name", "gender",
            "date_of_birth", "phone", "parent_phone", "email", "address", "section",
            "admission_date", "status", "image", "remarks",
        )
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "admission_date": forms.DateInput(attrs={"type": "date"})}


class SubjectForm(StyledModelForm):
    class Meta:
        model = Subject
        fields = ("name", "code", "description", "is_active")


class ClassSubjectForm(StyledModelForm):
    class Meta:
        model = ClassSubject
        fields = ("academic_class", "subject", "is_active")


class TeachingAssignmentForm(StyledModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ("teacher", "class_subject", "section", "is_active")

    def clean(self):
        cleaned = super().clean()
        class_subject, section = cleaned.get("class_subject"), cleaned.get("section")
        if class_subject and section and section.class_obj_id != class_subject.academic_class_id:
            raise forms.ValidationError("The section must belong to the selected academic class.")
        return cleaned


User = get_user_model()


class TeacherUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ("username", "password", "first_name", "last_name", "email", "phone")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists. Choose a different username.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = "TEACHER"
        if commit:
            user.save()
        return user


class TeacherProfileForm(StyledModelForm):
    class Meta:
        model = Teacher
        fields = ("employee_id", "qualification", "joining_date", "phone", "address", "is_active")
        widgets = {"joining_date": forms.DateInput(attrs={"type": "date"})}


class TeacherEditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")


@transaction.atomic
def save_teacher(user_form, teacher_form, teacher=None):
    user = user_form.save(commit=False)
    user.set_password(user_form.cleaned_data["password"]) if "password" in user_form.cleaned_data else None
    user.role = "TEACHER"
    user.save()
    teacher = teacher_form.save(commit=False)
    teacher.user = user
    teacher.save()
    return teacher
