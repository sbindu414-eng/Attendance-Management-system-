"""
manager.py
----------
Core business logic for the Attendance Management System.

The AttendanceManager class owns two in-memory data structures:

    self.students   : Dict[str, Student]              roll_no -> Student
    self.attendance : Dict[str, Dict[str, str]]        date -> {roll_no: 'P'/'A'}

and exposes methods for adding/removing students, marking attendance,
producing reports (date-wise and percentage/shortage), searching,
sorting, exporting to CSV, and saving/loading everything as JSON.

Keeping all of this in one class (rather than free functions acting
on global variables) means the CLI layer just creates one
AttendanceManager instance and calls methods on it - a straightforward
example of encapsulation.
"""

import csv
import math
import os
from typing import Dict, List, Optional, Tuple

from .models import Student
from .exceptions import (
    DuplicateStudentError,
    StudentNotFoundError,
    InvalidDateError,
    InvalidAttendanceStatusError,
)
from .validators import is_valid_date, is_valid_status
from . import storage


class AttendanceManager:
    """Owns the roster and attendance records and implements all
    supported operations on them."""

    DEFAULT_THRESHOLD = 75.0

    def __init__(self, students_file: str, attendance_file: str,
                 threshold: float = DEFAULT_THRESHOLD):
        self.students_file = students_file
        self.attendance_file = attendance_file
        self.threshold = threshold

        self.students: Dict[str, Student] = {}
        self.attendance: Dict[str, Dict[str, str]] = {}

        self.load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load students and attendance records from their JSON files."""
        raw_students = storage.load_json(self.students_file, [])
        self.students = {}
        for entry in raw_students:
            try:
                student = Student.from_dict(entry)
                self.students[student.roll_no] = student
            except (KeyError, TypeError):
                # Skip malformed entries rather than crashing the app.
                continue

        self.attendance = storage.load_json(self.attendance_file, {})

    def save(self) -> None:
        """Persist the current in-memory state to disk as JSON."""
        storage.save_json(
            self.students_file,
            [s.to_dict() for s in self.students.values()],
        )
        storage.save_json(self.attendance_file, self.attendance)

    # ------------------------------------------------------------------
    # Student management
    # ------------------------------------------------------------------
    def add_student(self, roll_no: str, name: str) -> Student:
        """Add a new student to the roster.

        Raises:
            InvalidInputError-derived exceptions are NOT raised here;
            callers are expected to validate roll_no/name with the
            validators module first. This method itself only checks
            for duplicates, keeping a single responsibility.
            DuplicateStudentError: if the roll number is already used.
        """
        roll_no = roll_no.strip().upper()
        name = name.strip()
        if roll_no in self.students:
            raise DuplicateStudentError(f"Roll number '{roll_no}' already exists.")
        student = Student(roll_no=roll_no, name=name)
        self.students[roll_no] = student
        return student

    def remove_student(self, roll_no: str) -> Student:
        """Remove a student and all of their attendance records.

        Raises:
            StudentNotFoundError: if the roll number does not exist.
        """
        roll_no = roll_no.strip().upper()
        if roll_no not in self.students:
            raise StudentNotFoundError(f"Roll number '{roll_no}' not found.")
        student = self.students.pop(roll_no)
        for date_records in self.attendance.values():
            date_records.pop(roll_no, None)
        return student

    def list_students(self) -> List[Student]:
        """Return all students sorted by roll number."""
        return sorted(self.students.values(), key=lambda s: s.roll_no)

    def search_students(self, keyword: str) -> List[Student]:
        """Case-insensitive search over roll number and name."""
        keyword = keyword.strip().lower()
        if not keyword:
            return self.list_students()
        return [
            s for s in self.list_students()
            if keyword in s.roll_no.lower() or keyword in s.name.lower()
        ]

    # ------------------------------------------------------------------
    # Attendance marking
    # ------------------------------------------------------------------
    def mark_attendance(self, roll_no: str, date: str, status: str) -> None:
        """Mark one student's attendance for one date.

        Raises:
            StudentNotFoundError, InvalidDateError, InvalidAttendanceStatusError
        """
        roll_no = roll_no.strip().upper()
        date = date.strip()
        status = status.strip().upper()

        if roll_no not in self.students:
            raise StudentNotFoundError(f"Roll number '{roll_no}' not found.")
        if not is_valid_date(date):
            raise InvalidDateError(f"'{date}' is not a valid date (expected YYYY-MM-DD).")
        if not is_valid_status(status):
            raise InvalidAttendanceStatusError(f"'{status}' is not valid. Use P or A.")

        self.attendance.setdefault(date, {})[roll_no] = status

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def date_report(self, date: str) -> List[Tuple[Student, Optional[str]]]:
        """Return (Student, status-or-None) for every student on `date`.

        Raises:
            InvalidDateError: if the date string is malformed.
        """
        date = date.strip()
        if not is_valid_date(date):
            raise InvalidDateError(f"'{date}' is not a valid date (expected YYYY-MM-DD).")
        day_records = self.attendance.get(date, {})
        return [(s, day_records.get(s.roll_no)) for s in self.list_students()]

    def student_stats(self, roll_no: str) -> Tuple[int, int, Optional[float]]:
        """Return (days_present, days_recorded, percentage_or_None) for a student.

        Raises:
            StudentNotFoundError: if the roll number does not exist.
        """
        roll_no = roll_no.strip().upper()
        if roll_no not in self.students:
            raise StudentNotFoundError(f"Roll number '{roll_no}' not found.")

        present = 0
        total = 0
        for records in self.attendance.values():
            if roll_no in records:
                total += 1
                if records[roll_no] == "P":
                    present += 1

        percentage = (present / total * 100) if total else None
        return present, total, percentage

    def percentage_report(self, sort_by: str = "roll_no", descending: bool = False) -> List[dict]:
        """Build a full attendance-percentage report for every student.

        Args:
            sort_by: one of 'roll_no', 'name', 'percentage'.
            descending: sort order.

        Returns:
            A list of dicts, one per student, each containing:
            roll_no, name, present, total, percentage (float or None),
            shortage (bool).
        """
        rows = []
        for student in self.students.values():
            present, total, percentage = self.student_stats(student.roll_no)
            rows.append({
                "roll_no": student.roll_no,
                "name": student.name,
                "present": present,
                "total": total,
                "percentage": percentage,
                "shortage": percentage is not None and percentage < self.threshold,
            })

        def sort_key(row):
            if sort_by == "name":
                return row["name"].lower()
            if sort_by == "percentage":
                # None percentages sort last regardless of direction
                return (row["percentage"] is None, row["percentage"] or -1)
            return row["roll_no"]

        rows.sort(key=sort_key, reverse=descending)
        return rows

    def shortage_list(self) -> List[dict]:
        """Convenience wrapper: students currently below the threshold."""
        return [row for row in self.percentage_report() if row["shortage"]]

    def shortage_message(self, roll_no: str) -> str:
        """Human-readable note on how far a student is from the threshold."""
        present, total, percentage = self.student_stats(roll_no)
        if total == 0:
            return "No attendance records yet."

        required_fraction = self.threshold / 100
        if percentage >= self.threshold:
            max_skippable = int(present / required_fraction - total)
            if max_skippable > 0:
                return (f"Can miss {max_skippable} more class"
                        f"{'es' if max_skippable != 1 else ''} and stay "
                        f"at or above {self.threshold:g}%.")
            return "At the edge of the threshold - no more absences allowed."

        # Below threshold: how many more PRESENT days needed to reach it,
        # assuming every future day attended is a 'P'.
        # (present + x) / (total + x) >= threshold/100  =>  solve for x
        numerator = required_fraction * total - present
        denominator = 1 - required_fraction
        needed = math.ceil(numerator / denominator) if denominator > 0 else 0
        needed = max(needed, 0)
        return (f"Needs {needed} more present day{'s' if needed != 1 else ''} "
                f"in a row to reach {self.threshold:g}%.")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_percentage_csv(self, path: str) -> None:
        """Write the percentage report to a CSV file."""
        rows = self.percentage_report(sort_by="roll_no")
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Roll No", "Name", "Present", "Total", "Percentage", "Status"])
            for row in rows:
                pct_display = f"{row['percentage']:.2f}" if row["percentage"] is not None else "N/A"
                if row["percentage"] is None:
                    status = "No Data"
                elif row["shortage"]:
                    status = "Shortage"
                else:
                    status = "OK"
                writer.writerow([row["roll_no"], row["name"], row["present"],
                                  row["total"], pct_display, status])
