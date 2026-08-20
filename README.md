# Attendance-Management-system-
 student attendance management application

# Attendance Management System

A menu-driven, console-based Python application for tracking daily
student attendance, calculating attendance percentages, and flagging
students who fall short of a minimum attendance requirement.

## Problem Statement

Teachers and class coordinators need a simple way to record who was
present or absent each day, and to periodically check which students
have fallen below the attendance percentage their institution
requires (a common "shortage" threshold, e.g. 75%). Doing this by
hand in a notebook or spreadsheet is error-prone and makes it hard to
answer questions like "how many more classes does this student need
to attend to clear their shortage?"

## Objective

Build a functional, well-tested, offline command-line application
that lets a user:

- maintain a roster of students,
- mark each student present (`P`) or absent (`A`) for a given date,
- view attendance for a specific date,
- view every student's overall attendance percentage,
- automatically identify students below a configurable threshold and
  tell them how many classes they need to attend (or can safely
  miss) to reach it,
- persist all of this data between runs, and
- export a summary report to CSV for use in a spreadsheet.

## Features

| # | Feature | Notes |
|---|---------|-------|
| 1 | Add / remove students | Roll number must be unique; removing a student also removes their attendance history |
| 2 | View / search roster | Case-insensitive search by roll number or name |
| 3 | Mark attendance | One date at a time, looping over roll numbers; re-marking a date overwrites the previous value |
| 4 | Date-wise report | Present / Absent / Unmarked counts for a chosen date |
| 5 | Percentage & shortage report | Sortable by roll number, name, or percentage; ascending or descending |
| 6 | Configurable threshold | Default 75%, changeable at runtime |
| 7 | Shortage guidance | Tells a student exactly how many more days they need (if below threshold) or can miss (if above) |
| 8 | CSV export | Percentage report can be exported for use in Excel/Sheets |
| 9 | Data persistence | Roster and attendance are saved as JSON after every action and on exit |
| 10 | Input validation | Roll numbers, names, dates, and P/A status are all validated before use |
| 11 | Exception handling | Custom exceptions for duplicate/missing students, bad dates, bad status; corrupted or missing data files are handled gracefully |

## Technologies Used

- **Python 3.9+** (standard library only — no third-party packages required)
  - `json` — data persistence
  - `csv` — report export
  - `dataclasses` — the `Student` model
  - `datetime` — date validation
  - `unittest` — automated test suite
- No paid tools, APIs, or hosting are used anywhere in this project (zero-cost requirement).

## Installation / Setup

1. Make sure Python 3.9 or newer is installed:
   ```bash
   python3 --version
   ```
2. Clone or copy this project folder to your machine.
3. No `pip install` is required — the project only uses the Python
   standard library.

## How to Run

From the project's root folder (the one containing `main.py`):

```bash
python3 main.py
```

You'll see a numbered menu. Enter the number of the action you want
and follow the prompts. Data is automatically saved to the `data/`
folder after every action and again when you choose `0` to exit.

### Quick walkthrough

```
1  -> Add student        (enter roll number, then name)
5  -> Mark attendance    (enter a date, then roll number + P/A pairs)
6  -> Date-wise report   (enter a date to see who was present/absent)
7  -> Percentage report  (see % and shortage list for everyone)
9  -> Export to CSV      (writes into the exports/ folder)
0  -> Save and exit
```

## Project Structure

```
attendance_management_system/
├── main.py                          # CLI entry point (menus, input, printing)
├── attendance_system/                # Core package (business logic)
│   ├── __init__.py
│   ├── models.py                    # Student dataclass
│   ├── validators.py                # Input validation helpers
│   ├── exceptions.py                # Custom exception classes
│   ├── manager.py                   # AttendanceManager (core logic)
│   └── storage.py                   # JSON load/save helpers
├── data/
│   ├── students.json                # Persisted roster
│   └── attendance.json              # Persisted attendance records
├── exports/                          # CSV reports land here
├── tests/
│   ├── __init__.py
│   └── test_attendance_system.py    # unittest suite (26 tests)
├── screenshots/                      # Demonstration screenshots
├── README.md
├── PROJECT_REPORT.md
└── TEST_CASES.md
```

### Why this structure?

The CLI layer (`main.py`) only handles user interaction: printing
menus, reading input, looping until input is valid, and calling into
the `attendance_system` package. All of the actual logic — validation
rules, the data model, business rules like "what counts as a
shortage" — lives in the package, completely independent of how the
user interacts with it. This separation is what makes the automated
tests possible: the tests import `AttendanceManager` directly and
never have to simulate typing into a menu.

## Testing

An automated test suite is provided using Python's built-in
`unittest` framework (no extra install needed):

```bash
python3 -m unittest discover -s tests -v
```

This runs 26 tests covering normal, invalid, boundary, duplicate, and
missing-data scenarios. See `TEST_CASES.md` for a written summary of
at least five representative cases, and `screenshots/` for a
screenshot of the full suite passing.

The suite uses `tempfile` to create throwaway JSON files for each
test, so running it never touches the real `data/` files used by the
actual application.

## Limitations

- Single-user, local, offline application — there is no login system
  or multi-teacher/multi-class support.
- Attendance is tracked as a simple daily P/A value; there's no
  support for partial-day or period-wise attendance.
- No GUI — this is a terminal/console application by design, in line
  with the assignment's focus on core Python fundamentals.
- Data files are plain JSON with no encryption; anyone with file
  access on the machine can read them.

## Future Improvements

- Add a simple GUI (e.g. with `tkinter`) or a web front-end.
- Support multiple classes/subjects, each with its own roster and
  attendance history.
- Add date-range reports (e.g. "attendance for the whole of August").
- Support editing a student's name without needing to remove and
  re-add them.
- Migrate storage to SQLite for larger datasets and more powerful
  querying, while keeping the same `AttendanceManager` interface.
- Add an "undo" for the last attendance mark.
