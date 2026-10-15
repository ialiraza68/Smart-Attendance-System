from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    AcademicClassForm, AcademicSessionForm, ClassSubjectForm, ProgramForm,
    SectionForm, StudentForm, SubjectForm, TeacherEditUserForm,
    TeacherProfileForm, TeacherUserForm, TeachingAssignmentForm, save_teacher,
    AttendanceCorrectionForm, AttendanceFilterForm,
)
from .models import (
    AcademicClass, AcademicSession, AttendanceCorrection, AttendanceRecord,
    AttendanceSession, ClassSubject, Program, Section, Student, Subject,
    Teacher, TeachingAssignment,
)

User = get_user_model()


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if not (request.user.is_superuser or request.user.role in roles):
                messages.error(request, "You do not have permission to access that page.")
                return redirect("dashboard")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def _page(request, queryset, template, context, page_size=10):
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(request.GET.get("page"))
    context.update({"page_obj": page_obj, "is_paginated": page_obj.has_other_pages(), "query": request.GET.get("q", "")})
    return render(request, template, context)


def _form_view(request, form_class, template, redirect_name, instance=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Changes saved successfully.")
        return redirect(redirect_name)
    return render(request, template, {"form": form, "active_page": redirect_name})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
        if user:
            login(request, user)
            return redirect(request.GET.get("next") or "dashboard")
        error = "Invalid username or password."
    return render(request, "registration/login.html", {"error": error})


@require_POST
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")


@login_required
def dashboard(request):
    if request.user.role == "TEACHER":
        return teacher_dashboard(request)
    return admin_dashboard(request)


@role_required("ADMIN")
def admin_dashboard(request):
    active_session = AcademicSession.objects.filter(is_active=True).first()
    today_sessions = AttendanceSession.objects.filter(date=date.today())
    all_students = Student.objects.all()
    all_classes = AcademicClass.objects.filter(is_active=True)
    all_sections = Section.objects.filter(is_active=True)
    student_queryset = all_students
    class_queryset = all_classes
    if active_session:
        student_queryset = student_queryset.filter(section__class_obj__session=active_session)
        class_queryset = class_queryset.filter(session=active_session)

    sections = list(
        Section.objects.filter(is_active=True, class_obj__is_active=True)
        .filter(class_obj__session=active_session) if active_session else
        Section.objects.filter(is_active=True, class_obj__is_active=True)
    )
    sections = list(
        Section.objects.filter(pk__in=[section.pk for section in sections])
        .annotate(active_student_count=Count("students", filter=Q(students__status="ACTIVE")))
        .select_related("class_obj__program", "class_obj__session")
    )
    for section in sections:
        section.capacity_percent = min(round(section.active_student_count * 100 / section.capacity), 100) if section.capacity else 0
        section.capacity_class = "danger" if section.capacity_percent >= 100 else "warning" if section.capacity_percent >= 80 else ""

    recent_assignments = TeachingAssignment.objects.filter(is_active=True).select_related(
        "teacher__user", "class_subject__subject", "class_subject__academic_class__program",
        "class_subject__academic_class__session", "section",
    ).order_by("-assigned_at")[:5]
    return render(request, "Admin/dashboard.html", {
        "active_page": "dashboard",
        "active_session": active_session,
        "total_students": all_students.count(),
        "active_students": all_students.filter(status="ACTIVE").count(),
        "total_teachers": Teacher.objects.filter(is_active=True).count(),
        "total_assignments": TeachingAssignment.objects.filter(is_active=True).count(),
        "total_classes": all_classes.count(),
        "total_sections": all_sections.count(),
        "total_subjects": Subject.objects.filter(is_active=True).count(),
        "total_programs": Program.objects.filter(is_active=True).count(),
        "recent_students": student_queryset.select_related("section__class_obj__program", "section__class_obj__session").order_by("-created_at")[:5],
        "capacity_sections": sections[:5],
        "recent_assignments": recent_assignments,
        "attendance_submitted_today": today_sessions.filter(status="SUBMITTED").count(),
        "attendance_draft_today": today_sessions.filter(status="DRAFT").count(),
        "attendance_present_today": AttendanceRecord.objects.filter(
            session__date=date.today(), status="PRESENT"
        ).count(),
    })


@role_required("TEACHER", "ADMIN")
def teacher_dashboard(request):
    assignments = TeachingAssignment.objects.select_related("class_subject__subject", "class_subject__academic_class__program", "class_subject__academic_class__session", "section").filter(is_active=True)
    if request.user.role == "TEACHER":
        assignments = assignments.filter(teacher__user=request.user)
    return render(request, "Teacher/dashboard.html", {
        "active_page": "teacher_dashboard", "active_session": AcademicSession.objects.filter(is_active=True).first(),
        "assignments": assignments, "assigned_classes": assignments.values("section_id").distinct().count(),
        "student_count": Student.objects.filter(section__teaching_assignments__in=assignments, status="ACTIVE").distinct().count(),
        "subject_count": assignments.values("class_subject__subject_id").distinct().count(),
    })


@role_required("ADMIN")
def sessions(request):
    qs = AcademicSession.objects.all()
    q = request.GET.get("q", "")
    return _page(request, qs.filter(name__icontains=q), "Admin/sessions/list.html", {"active_page": "sessions", "sessions": qs})


@role_required("ADMIN")
def session_create(request):
    return _form_view(request, AcademicSessionForm, "Admin/sessions/create.html", "sessions")


@role_required("ADMIN")
def session_edit(request, pk):
    return _form_view(request, AcademicSessionForm, "Admin/sessions/create.html", "sessions", get_object_or_404(AcademicSession, pk=pk))


@role_required("ADMIN")
@require_POST
def session_delete(request, pk):
    return _delete_record(request, AcademicSession, pk, "sessions", "Academic session")


@role_required("ADMIN")
def session_detail(request, pk):
    session = get_object_or_404(AcademicSession, pk=pk)
    return render(request, "Admin/sessions/detail.html", {"active_page": "sessions", "session": session, "classes": session.classes.select_related("program")})


@role_required("ADMIN")
def programs(request):
    qs = Program.objects.filter(Q(name__icontains=request.GET.get("q", "")) | Q(description__icontains=request.GET.get("q", "")))
    return _page(request, qs, "Admin/programs/list.html", {"active_page": "programs", "programs": qs})


@role_required("ADMIN")
def program_create(request, pk=None):
    return _form_view(request, ProgramForm, "Admin/programs/create.html", "programs", get_object_or_404(Program, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def program_delete(request, pk):
    return _delete_record(request, Program, pk, "programs", "Program")


@role_required("ADMIN")
def classes(request):
    qs = AcademicClass.objects.select_related("session", "program").filter(Q(program__name__icontains=request.GET.get("q", "")) | Q(session__name__icontains=request.GET.get("q", "")))
    return _page(request, qs, "Admin/classes/list.html", {"active_page": "classes", "classes": qs})


@role_required("ADMIN")
def class_create(request, pk=None):
    return _form_view(request, AcademicClassForm, "Admin/classes/create.html", "classes", get_object_or_404(AcademicClass, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def class_delete(request, pk):
    return _delete_record(request, AcademicClass, pk, "classes", "Academic class")


@role_required("ADMIN")
def sections(request):
    qs = Section.objects.select_related("class_obj__program", "class_obj__session").filter(Q(name__icontains=request.GET.get("q", "")) | Q(class_obj__program__name__icontains=request.GET.get("q", "")))
    return _page(request, qs, "Admin/sections/list.html", {"active_page": "sections", "sections": qs})


@role_required("ADMIN")
def section_create(request, pk=None):
    return _form_view(request, SectionForm, "Admin/sections/create.html", "sections", get_object_or_404(Section, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    section_name = str(section)
    if section.students.exists():
        messages.error(request, f"Section '{section_name}' cannot be deleted while it has enrolled students.")
        return redirect("sections")
    try:
        with transaction.atomic():
            section.delete()
    except ProtectedError:
        messages.error(request, f"Section '{section_name}' cannot be deleted because it is still in use.")
    else:
        messages.success(request, f"Section '{section_name}' was deleted.")
    return redirect("sections")


@role_required("ADMIN")
def students(request):
    q = request.GET.get("q", "")
    qs = Student.objects.select_related("section__class_obj__program", "section__class_obj__session").filter(Q(name__icontains=q) | Q(roll_number__icontains=q) | Q(registration_number__icontains=q))
    if request.GET.get("status"):
        qs = qs.filter(status=request.GET["status"].upper())
    return _page(request, qs, "Admin/students/list.html", {"active_page": "students", "students": qs})


@role_required("ADMIN")
def student_create(request, pk=None):
    return _form_view(request, StudentForm, "Admin/students/create.html", "students", get_object_or_404(Student, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student_name = student.name
    with transaction.atomic():
        student.delete()
    messages.success(request, f"Student '{student_name}' was deleted.")
    return redirect("students")


@role_required("ADMIN", "TEACHER")
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("section__class_obj__program"), pk=pk)
    if request.user.role == "TEACHER" and not TeachingAssignment.objects.filter(teacher__user=request.user, section=student.section, is_active=True).exists():
        messages.error(request, "You can only view students in your assigned sections.")
        return redirect("teacher_students")
    return render(request, "Admin/students/detail.html" if request.user.role == "ADMIN" else "Teacher/students/detail.html", {"student": student, "active_page": "students"})


@role_required("ADMIN")
def subjects(request):
    q = request.GET.get("q", "")
    qs = Subject.objects.filter(Q(name__icontains=q) | Q(code__icontains=q))
    return _page(request, qs, "Admin/subjects/list.html", {"active_page": "subjects", "subjects": qs})


@role_required("ADMIN")
def subject_create(request, pk=None):
    return _form_view(request, SubjectForm, "Admin/subjects/create.html", "subjects", get_object_or_404(Subject, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def subject_delete(request, pk):
    return _delete_record(request, Subject, pk, "subjects", "Subject")


@role_required("ADMIN")
def class_subjects(request):
    qs = ClassSubject.objects.select_related("academic_class__program", "academic_class__session", "subject")
    return _page(request, qs, "Admin/class_subjects/list.html", {"active_page": "class_subjects", "class_subjects": qs})


@role_required("ADMIN")
def class_subject_create(request, pk=None):
    return _form_view(request, ClassSubjectForm, "Admin/class_subjects/create.html", "class_subjects", get_object_or_404(ClassSubject, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def class_subject_delete(request, pk):
    return _delete_record(request, ClassSubject, pk, "class_subjects", "Class subject")


@role_required("ADMIN")
def teachers(request):
    q = request.GET.get("q", "")
    users = list(
        Teacher.objects.select_related("user")
        .filter(
            Q(employee_id__icontains=q)
            | Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__email__icontains=q)
        )
    )
    profile_user_ids = {teacher.user_id for teacher in users}
    orphan_users = list(
        User.objects.filter(role="TEACHER")
        .exclude(pk__in=profile_user_ids)
        .filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    )
    rows = [{"teacher": teacher, "user": teacher.user, "has_profile": True} for teacher in users]
    rows.extend({"teacher": None, "user": user, "has_profile": False} for user in orphan_users)
    rows.sort(key=lambda row: (row["user"].last_name or "", row["user"].first_name or "", row["user"].username.lower()))
    return _page(request, rows, "Admin/teachers/list.html", {"active_page": "teachers", "teacher_count": len(rows)})


@role_required("ADMIN")
def teacher_create(request, pk=None):
    teacher = get_object_or_404(Teacher.objects.select_related("user"), pk=pk) if pk else None
    user_form = TeacherEditUserForm(request.POST or None, instance=teacher.user) if teacher else TeacherUserForm(request.POST or None)
    teacher_form = TeacherProfileForm(request.POST or None, instance=teacher)
    if request.method == "POST" and user_form.is_valid() and teacher_form.is_valid():
        save_teacher(user_form, teacher_form, teacher)
        messages.success(request, "Teacher profile saved successfully.")
        return redirect("teachers")
    return render(request, "Admin/teachers/create.html", {"user_form": user_form, "teacher_form": teacher_form, "teacher": teacher, "active_page": "teachers"})


@role_required("ADMIN")
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related("user"), pk=pk)
    assignments = TeachingAssignment.objects.filter(teacher=teacher).select_related(
        "class_subject__subject", "class_subject__academic_class__program", "section",
    )
    return render(request, "Admin/teachers/detail.html", {"teacher": teacher, "assignments": assignments, "active_page": "teachers"})


@role_required("ADMIN")
@require_POST
def teacher_delete(request, user_pk):
    user = get_object_or_404(User, pk=user_pk, role="TEACHER")
    username = user.username
    with transaction.atomic():
        user.delete()
    messages.success(request, f"Teacher account '{username}' was deleted.")
    return redirect("teachers")


@role_required("ADMIN")
def assignments(request):
    qs = TeachingAssignment.objects.select_related("teacher__user", "class_subject__subject", "class_subject__academic_class__program", "section")
    return _page(request, qs, "Admin/assignments/list.html", {"active_page": "assignments", "assignments": qs})


@role_required("ADMIN")
def assignment_create(request, pk=None):
    return _form_view(request, TeachingAssignmentForm, "Admin/assignments/create.html", "assignments", get_object_or_404(TeachingAssignment, pk=pk) if pk else None)


@role_required("ADMIN")
@require_POST
def assignment_delete(request, pk):
    return _delete_record(request, TeachingAssignment, pk, "assignments", "Teaching assignment")


def _delete_record(request, model, pk, redirect_name, label):
    record = get_object_or_404(model, pk=pk)
    record_name = str(record)
    try:
        with transaction.atomic():
            record.delete()
    except ProtectedError:
        messages.error(request, f"{label} '{record_name}' cannot be deleted because it is still in use.")
    else:
        messages.success(request, f"{label} '{record_name}' was deleted.")
    return redirect(redirect_name)


@role_required("TEACHER")
def teacher_profile(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    form = TeacherProfileForm(request.POST or None, instance=teacher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("teacher_profile")
    return render(request, "Teacher/profile.html", {"form": form, "teacher": teacher, "active_page": "teacher_profile"})


@role_required("TEACHER")
def teacher_assignments(request):
    qs = TeachingAssignment.objects.select_related("class_subject__subject", "section", "class_subject__academic_class__program").filter(teacher__user=request.user, is_active=True)
    return _page(request, qs, "Teacher/assignments/list.html", {"assignments": qs, "active_page": "teacher_assignments"})


@role_required("TEACHER")
def teacher_classes(request):
    return render(request, "Teacher/classes/list.html", {"assignments": TeachingAssignment.objects.filter(teacher__user=request.user, is_active=True).select_related("section__class_obj__program"), "active_page": "teacher_classes"})


@role_required("TEACHER")
def teacher_students(request):
    sections = TeachingAssignment.objects.filter(teacher__user=request.user, is_active=True).values("section_id")
    q = request.GET.get("q", "")
    qs = Student.objects.filter(section_id__in=sections).filter(Q(name__icontains=q) | Q(roll_number__icontains=q)).select_related("section__class_obj__program")
    return _page(request, qs, "Teacher/students/list.html", {"students": qs, "active_page": "teacher_students"})


@role_required("TEACHER")
def teacher_subjects(request):
    subjects = Subject.objects.filter(
        class_subjects__teaching_assignments__teacher__user=request.user,
        class_subjects__teaching_assignments__is_active=True,
    ).distinct()
    subject_rows = []
    for subject in subjects:
        assignments = TeachingAssignment.objects.filter(
            teacher__user=request.user,
            class_subject__subject=subject,
            is_active=True,
        ).select_related("section")
        subject.assigned_sections = assignments.count()
        subject.assigned_students = Student.objects.filter(
            section__teaching_assignments__in=assignments,
            status="ACTIVE",
        ).distinct().count()
        subject_rows.append(subject)
    return render(request, "Teacher/subjects/list.html", {"subjects": subject_rows, "active_page": "teacher_subjects"})


def _attendance_sections(request):
    sections = Section.objects.filter(is_active=True, class_obj__is_active=True)
    if request.user.role == "TEACHER":
        sections = sections.filter(
            teaching_assignments__teacher__user=request.user,
            teaching_assignments__is_active=True,
        )
    return sections.select_related("class_obj__program", "class_obj__session").distinct()


def _attendance_session_queryset(request):
    qs = AttendanceSession.objects.select_related(
        "section__class_obj__program", "section__class_obj__session", "taken_by__user"
    ).annotate(
        student_count=Count("records"),
        present_count=Count("records", filter=Q(records__status="PRESENT")),
        absent_count=Count("records", filter=Q(records__status="ABSENT")),
        leave_count=Count("records", filter=Q(records__status="LEAVE")),
    )
    if request.user.role == "TEACHER":
        qs = qs.filter(
            section__teaching_assignments__teacher__user=request.user,
            section__teaching_assignments__is_active=True,
        )
    return qs.distinct()


def _teacher_can_access_section(request, section):
    return request.user.is_superuser or request.user.role == "ADMIN" or TeachingAssignment.objects.filter(
        teacher__user=request.user, section=section, is_active=True,
        teacher__is_active=True,
    ).exists()


@role_required("TEACHER", "ADMIN")
def attendance_dashboard(request):
    today = date.today()
    sessions = _attendance_session_queryset(request)
    sections = _attendance_sections(request)
    today_sessions = sessions.filter(date=today)
    return render(request, "attendance/dashboard.html", {
        "active_page": "attendance_dashboard",
        "sections": sections,
        "today_sessions": today_sessions,
        "section_count": sections.count(),
        "student_count": Student.objects.filter(section__in=sections, status="ACTIVE").distinct().count(),
        "submitted_today": today_sessions.filter(status="SUBMITTED").count(),
        "draft_today": today_sessions.filter(status="DRAFT").count(),
        "present_today": today_sessions.filter(date=today, records__status="PRESENT").count(),
        "absent_today": today_sessions.filter(date=today, records__status="ABSENT").count(),
        "leave_today": today_sessions.filter(date=today, records__status="LEAVE").count(),
    })


@role_required("TEACHER")
def attendance_take(request, section_id=None, session_id=None):
    if section_id is None:
        raw_section_id = request.POST.get("section_id") or request.GET.get("section_id")
        if raw_section_id:
            try:
                section_id = int(raw_section_id)
            except (TypeError, ValueError):
                section_id = None
    sections = _attendance_sections(request)
    selected_section = get_object_or_404(sections, pk=section_id) if section_id else None
    selected_date = request.POST.get("date") or request.GET.get("date") or date.today().isoformat()
    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()
    future_requested = selected_date > date.today()
    if future_requested:
        messages.error(request, "Attendance date cannot be in the future.")
        selected_date = date.today()
    session = None
    if session_id:
        session = get_object_or_404(AttendanceSession, pk=session_id)
        if not _teacher_can_access_section(request, session.section):
            return redirect("dashboard")
        selected_section = session.section
    elif selected_section:
        session = AttendanceSession.objects.filter(section=selected_section, date=selected_date).first()
    students = Student.objects.filter(section=selected_section, status="ACTIVE").order_by("roll_number") if selected_section else Student.objects.none()
    records = {record.student_id: record for record in session.records.all()} if session else {}
    if request.method == "POST" and selected_section and not future_requested:
        action = request.POST.get("action", "draft")
        statuses = {}
        invalid = False
        for student in students:
            status = request.POST.get(f"status_{student.pk}", "")
            if status not in dict(AttendanceRecord.STATUS_CHOICES):
                invalid = True
            statuses[student.pk] = status
        if action == "submit" and (invalid or len(statuses) != students.count() or any(not value for value in statuses.values())):
            messages.error(request, "Every eligible student must have a valid attendance status before submission.")
        elif invalid:
            messages.error(request, "Attendance contains an invalid status.")
        else:
            try:
                with transaction.atomic():
                    session, created = AttendanceSession.objects.select_for_update().get_or_create(
                        section=selected_section,
                        date=selected_date,
                        defaults={"taken_by": request.user.teacher_profile, "status": "DRAFT"},
                    )
                    if session.status in {"LOCKED", "SUBMITTED"}:
                        raise ValueError("This attendance session is no longer editable.")
                    session.taken_by = request.user.teacher_profile
                    session.status = "SUBMITTED" if action == "submit" else "DRAFT"
                    session.save(update_fields=["taken_by", "status", "updated_at"])
                    existing = {r.student_id: r for r in session.records.select_for_update()}
                    AttendanceRecord.objects.bulk_create([
                        AttendanceRecord(
                            session=session, student=student, status=statuses[student.pk],
                            remarks=request.POST.get(f"remarks_{student.pk}", ""),
                            marked_by=request.user.teacher_profile,
                        )
                        for student in students if student.pk not in existing
                    ])
                    for student in students:
                        record = existing.get(student.pk)
                        if record:
                            record.status = statuses[student.pk]
                            record.remarks = request.POST.get(f"remarks_{student.pk}", "")
                            record.marked_by = request.user.teacher_profile
                    if existing:
                        AttendanceRecord.objects.bulk_update(
                            list(existing.values()), ["status", "remarks", "marked_by", "updated_at"]
                        )
            except (IntegrityError, ValueError) as exc:
                messages.error(request, str(exc) or "The attendance session could not be saved.")
            else:
                messages.success(request, "Attendance submitted." if action == "submit" else "Draft saved.")
                return redirect("attendance_take_session", session_id=session.pk)
    student_rows = [{"student": student, "record": records.get(student.pk)} for student in students]
    return render(request, "attendance/take.html", {
        "active_page": "attendance_take", "sections": sections,
        "selected_section": selected_section, "selected_date": selected_date,
        "session": session, "student_rows": student_rows,
        "statuses": dict(AttendanceRecord.STATUS_CHOICES),
    })


@role_required("TEACHER", "ADMIN")
def attendance_history(request):
    sections = _attendance_sections(request)
    form = AttendanceFilterForm(request.GET or None, sections=sections)
    sessions = _attendance_session_queryset(request)
    if form.is_valid():
        data = form.cleaned_data
        if data.get("date"):
            sessions = sessions.filter(date=data["date"])
        if data.get("start_date"):
            sessions = sessions.filter(date__gte=data["start_date"])
        if data.get("end_date"):
            sessions = sessions.filter(date__lte=data["end_date"])
        if data.get("section"):
            sessions = sessions.filter(section=data["section"])
        if data.get("status"):
            sessions = sessions.filter(status=data["status"])
    return render(request, "attendance/history.html", {
        "active_page": "attendance_history", "form": form,
        "sessions": sessions.order_by("-date", "section__name"),
    })


@role_required("TEACHER", "ADMIN")
def attendance_session_detail(request, session_id):
    session = get_object_or_404(_attendance_session_queryset(request), pk=session_id)
    records = session.records.select_related("student").order_by("student__roll_number")
    return render(request, "attendance/session_detail.html", {
        "active_page": "attendance_history", "session": session, "records": records,
    })


@role_required("ADMIN")
def admin_attendance_dashboard(request):
    return attendance_dashboard(request)


@role_required("ADMIN")
def attendance_lock(request, session_id):
    if request.method == "POST":
        session = get_object_or_404(AttendanceSession, pk=session_id)
        session.status = "LOCKED"
        session.save(update_fields=["status", "updated_at"])
        messages.success(request, "Attendance session locked.")
    return redirect("attendance_session_detail", session_id=session_id)


@role_required("ADMIN")
def attendance_reopen(request, session_id):
    if request.method == "POST":
        session = get_object_or_404(AttendanceSession, pk=session_id)
        session.status = "DRAFT"
        session.save(update_fields=["status", "updated_at"])
        messages.success(request, "Attendance session reopened for correction.")
    return redirect("attendance_session_detail", session_id=session_id)


@role_required("ADMIN")
def attendance_correct(request, record_id):
    record = get_object_or_404(AttendanceRecord.objects.select_related("session"), pk=record_id)
    form = AttendanceCorrectionForm(request.POST or None, initial={"status": record.status})
    if request.method == "POST" and form.is_valid():
        if record.session.status == "LOCKED":
            messages.error(request, "Unlock the session before correcting attendance.")
        else:
            with transaction.atomic():
                old_status = record.status
                record.status = form.cleaned_data["status"]
                record.save(update_fields=["status", "updated_at"])
                AttendanceCorrection.objects.create(
                    record=record, previous_status=old_status,
                    new_status=record.status, changed_by=request.user,
                    reason=form.cleaned_data["reason"],
                )
            messages.success(request, "Attendance correction recorded.")
            return redirect("attendance_session_detail", session_id=record.session_id)
    return render(request, "attendance/correct.html", {"form": form, "record": record, "active_page": "attendance_history"})
