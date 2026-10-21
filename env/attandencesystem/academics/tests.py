from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    AcademicClass, AcademicSession, AttendanceRecord, AttendanceSession,
    ClassSubject, Program, Section, Student, Subject, Teacher,
    TeachingAssignment,
)


class AttendanceWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.teacher_user = user_model.objects.create_user(
            username="teacher", password="password123", role="TEACHER"
        )
        self.other_user = user_model.objects.create_user(
            username="other", password="password123", role="TEACHER"
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user, employee_id="T-001"
        )
        self.other_teacher = Teacher.objects.create(
            user=self.other_user, employee_id="T-002"
        )
        academic_session = AcademicSession.objects.create(
            name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 6, 30)
        )
        program = Program.objects.create(name="Computer Science")
        academic_class = AcademicClass.objects.create(
            session=academic_session, program=program, year="1ST"
        )
        self.section = Section.objects.create(class_obj=academic_class, name="A")
        other_section = Section.objects.create(class_obj=academic_class, name="B")
        subject = Subject.objects.create(name="Math", code="MATH-1")
        class_subject = ClassSubject.objects.create(
            academic_class=academic_class, subject=subject
        )
        TeachingAssignment.objects.create(
            teacher=self.teacher, class_subject=class_subject, section=self.section
        )
        TeachingAssignment.objects.create(
            teacher=self.other_teacher, class_subject=class_subject, section=other_section
        )
        self.students = [
            Student.objects.create(
                roll_number=f"R-{index}", name=f"Student {index}",
                father_name="Parent", gender="MALE", parent_phone="000",
                section=self.section, admission_date=date(2026, 8, 1),
            )
            for index in range(1, 3)
        ]

    def login_teacher(self):
        self.client.force_login(self.teacher_user)

    def test_teacher_can_submit_complete_roster_once(self):
        self.login_teacher()
        response = self.client.post(
            reverse("attendance_take_section", args=[self.section.pk]),
            {
                "date": date.today().isoformat(),
                "action": "submit",
                **{
                    f"status_{student.pk}": "PRESENT"
                    for student in self.students
                },
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AttendanceSession.objects.count(), 1)
        self.assertEqual(AttendanceRecord.objects.count(), 2)

        response = self.client.post(
            reverse("attendance_take_section", args=[self.section.pk]),
            {
                "date": date.today().isoformat(),
                "action": "submit",
                **{
                    f"status_{student.pk}": "ABSENT"
                    for student in self.students
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AttendanceSession.objects.count(), 1)
        self.assertEqual(AttendanceRecord.objects.filter(status="ABSENT").count(), 0)

    def test_teacher_can_save_mixed_attendance_statuses(self):
        self.login_teacher()
        statuses = ["PRESENT", "LEAVE"]
        response = self.client.post(
            reverse("attendance_take_section", args=[self.section.pk]),
            {
                "date": date.today().isoformat(),
                "action": "submit",
                **{
                    f"status_{student.pk}": status
                    for student, status in zip(self.students, statuses)
                },
            },
        )

        self.assertEqual(response.status_code, 302)
        records = AttendanceRecord.objects.order_by("student_id")
        self.assertEqual(list(records.values_list("status", flat=True)), statuses)

    def test_selecting_section_loads_student_roster(self):
        self.login_teacher()
        response = self.client.get(
            reverse("attendance_take"),
            {"section_id": self.section.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.students[0].name)
        self.assertContains(response, self.students[1].name)

    def test_teacher_cannot_access_unassigned_section(self):
        self.login_teacher()
        response = self.client.get(reverse("attendance_take_section", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_incomplete_submission_does_not_create_session(self):
        self.login_teacher()
        response = self.client.post(
            reverse("attendance_take_section", args=[self.section.pk]),
            {
                "date": date.today().isoformat(),
                "action": "submit",
                f"status_{self.students[0].pk}": "PRESENT",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.exists())

    def test_future_date_is_rejected(self):
        self.login_teacher()
        future = date.today() + timedelta(days=1)
        response = self.client.post(
            reverse("attendance_take_section", args=[self.section.pk]),
            {
                "date": future.isoformat(),
                "action": "submit",
                **{
                    f"status_{student.pk}": "PRESENT"
                    for student in self.students
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceSession.objects.exists())
