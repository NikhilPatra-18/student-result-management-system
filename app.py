
import sqlite3
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Student Result Management System",
    page_icon="🎓",
    layout="wide"
)

DB_NAME = "student_results.db"


# DATABASE SETUP
def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                python_marks INTEGER NOT NULL,
                maths_marks INTEGER NOT NULL,
                dsa_marks INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                grade TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)


# CALCULATE RESULT
def calculate_result(python_marks, maths_marks, dsa_marks):
    marks = [python_marks, maths_marks, dsa_marks]
    total = sum(marks)
    percentage = total / 3

    if any(mark < 35 for mark in marks):
        grade = "F"
        status = "Fail"
    elif percentage >= 90:
        grade = "A+"
        status = "Pass"
    elif percentage >= 80:
        grade = "A"
        status = "Pass"
    elif percentage >= 70:
        grade = "B"
        status = "Pass"
    elif percentage >= 60:
        grade = "C"
        status = "Pass"
    elif percentage >= 50:
        grade = "D"
        status = "Pass"
    else:
        grade = "E"
        status = "Pass"

    return total, percentage, grade, status


# ADD STUDENT
def add_student(roll, name, course, p, m, d):
    total, percentage, grade, status = calculate_result(p, m, d)

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll, name, course, p, m, d,
            total, percentage, grade, status
        ))


# READ STUDENTS
def get_all_students():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM students ORDER BY roll_no", conn
        )


def get_student(roll):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM students WHERE roll_no = ?", (roll,)
        ).fetchone()


# UPDATE STUDENT
def update_student(roll, name, course, p, m, d):
    total, percentage, grade, status = calculate_result(p, m, d)

    with get_connection() as conn:
        conn.execute("""
            UPDATE students
            SET name=?, course=?, python_marks=?,
                maths_marks=?, dsa_marks=?, total=?,
                percentage=?, grade=?, status=?
            WHERE roll_no=?
        """, (
            name, course, p, m, d,
            total, percentage, grade, status, roll
        ))


# DELETE STUDENT
def delete_student(roll):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM students WHERE roll_no=?", (roll,)
        )


create_table()

st.title("🎓 Student Result Management System")
st.write("Manage student details, marks and academic results.")

df = get_all_students()

# DASHBOARD
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Students", len(df))
c2.metric(
    "Passed",
    int((df["status"] == "Pass").sum()) if not df.empty else 0
)
c3.metric(
    "Failed",
    int((df["status"] == "Fail").sum()) if not df.empty else 0
)
c4.metric(
    "Class Average",
    f"{df['percentage'].mean():.2f}%"
    if not df.empty else "0%"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Add Student",
    "Search Result",
    "All Results",
    "Update Student",
    "Delete Student"
])


# TAB 1: ADD STUDENT
with tab1:
    st.subheader("Add New Student")

    with st.form("add_form"):
        roll = st.text_input("Roll Number").strip()
        name = st.text_input("Student Name").strip()
        course = st.text_input("Course", value="CSE").strip()

        c1, c2, c3 = st.columns(3)
        p = c1.number_input("Python Marks", 0, 100, 0)
        m = c2.number_input("Mathematics Marks", 0, 100, 0)
        d = c3.number_input("DSA Marks", 0, 100, 0)

        submitted = st.form_submit_button("Save Student")

        if submitted:
            if not roll or not name or not course:
                st.error("Please fill in all details.")
            else:
                try:
                    add_student(
                        roll, name, course, int(p), int(m), int(d)
                    )
                    st.success("Student saved successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("This roll number already exists.")


# TAB 2: SEARCH RESULT
with tab2:
    st.subheader("Search Student")

    search_roll = st.text_input("Enter Roll Number", key="search")

    if st.button("Search Result"):
        if not search_roll.strip():
            st.warning("Enter a roll number.")
        else:
            student = get_student(search_roll.strip())

            if student:
                (
                    roll, name, course, p, m, d,
                    total, percentage, grade, status
                ) = student

                st.success("Student found!")
                st.write("**Name:**", name)
                st.write("**Roll Number:**", roll)
                st.write("**Course:**", course)

                c1, c2, c3 = st.columns(3)
                c1.metric("Total", f"{total}/300")
                c2.metric("Percentage", f"{percentage:.2f}%")
                c3.metric("Grade", grade)

                st.write("**Status:**", status)
                st.dataframe(pd.DataFrame({
                    "Subject": ["Python", "Mathematics", "DSA"],
                    "Marks": [p, m, d]
                }), use_container_width=True)
            else:
                st.error("Student not found.")


# TAB 3: ALL RESULTS
with tab3:
    st.subheader("All Student Results")

    if df.empty:
        st.info("No student records available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Results CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="student_results.csv",
            mime="text/csv"
        )


# TAB 4: UPDATE STUDENT
with tab4:
    st.subheader("Update Student Result")

    if df.empty:
        st.info("Add a student first.")
    else:
        selected = st.selectbox(
            "Select Roll Number",
            df["roll_no"].tolist(),
            key="update"
        )

        student = get_student(selected)

        if student:
            roll, old_name, old_course, old_p, old_m, old_d = student[:6]

            with st.form("update_form"):
                name = st.text_input("Student Name", value=old_name).strip()
                course = st.text_input("Course", value=old_course).strip()

                c1, c2, c3 = st.columns(3)
                p = c1.number_input(
                    "Python", 0, 100, int(old_p), key="up_p"
                )
                m = c2.number_input(
                    "Mathematics", 0, 100, int(old_m), key="up_m"
                )
                d = c3.number_input(
                    "DSA", 0, 100, int(old_d), key="up_d"
                )

                if st.form_submit_button("Update Result"):
                    if not name or not course:
                        st.error("Name and course are required.")
                    else:
                        update_student(
                            roll, name, course, int(p), int(m), int(d)
                        )
                        st.success("Student updated successfully!")
                        st.rerun()


# TAB 5: DELETE STUDENT
with tab5:
    st.subheader("Delete Student")

    if df.empty:
        st.info("No student records to delete.")
    else:
        selected = st.selectbox(
            "Select Student Roll Number",
            df["roll_no"].tolist(),
            key="delete"
        )

        student = get_student(selected)

        if student:
            st.warning(
                f"Selected student: {student[1]} "
                f"(Roll No: {student[0]})"
            )

            confirm = st.checkbox("Confirm deletion")

            if st.button("Delete Student"):
                if confirm:
                    delete_student(selected)
                    st.success("Student deleted.")
                    st.rerun()
                else:
                    st.error("Please confirm deletion first.")

st.divider()
st.caption("Built with Python, Streamlit and SQLite")
