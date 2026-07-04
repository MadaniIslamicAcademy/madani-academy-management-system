# =============================================================================
# MADANI ISLAMIC ACADEMY(R) LTD - MANAGEMENT SYSTEM
# -----------------------------------------------------------------------------
# Built with: Python + Streamlit (frontend) + SQLite (database)
# Everything lives in this single file: app.py
#
# What this app does:
#   - Dashboard  : summary cards + charts
#   - Students   : add / view / search / edit / delete students
#   - Teachers   : add / view teachers
#   - Fees       : add fee records / view paid fees / view pending fees
#
# Beginner note: read the comments (lines starting with #) to understand
# each section. You do NOT need to change anything to run it.
# =============================================================================

# ---- 1. IMPORT THE LIBRARIES WE NEED -----------------------------------------
import streamlit as st            # builds the web app (the frontend)
import sqlite3                    # the small built-in database engine
import pandas as pd              # handles tables of data nicely
import plotly.express as px      # draws the charts
from datetime import date        # lets us work with dates


# ---- 2. BASIC PAGE SETTINGS --------------------------------------------------
# This must be the FIRST Streamlit command in the script.
st.set_page_config(
    page_title="Madani Islamic Academy",
    page_icon="🕌",
    layout="wide",               # use the full width of the screen
)


# ---- 3. BRAND COLOURS (official Madani palette) ------------------------------
MAIN_GREEN   = "#135C26"
DARK_GREEN   = "#003919"
BRIGHT_YELLOW = "#F3F71C"
LIGHT_BG     = "#F8FFF5"
BODY_TEXT    = "#26332b"

# A little CSS to make the app match the Madani brand.
# (This is optional styling - the app works even if it is removed.)
st.markdown(f"""
<style>
    .stApp {{ background-color: {LIGHT_BG}; }}

    /* Headings in dark green */
    h1, h2, h3 {{ color: {DARK_GREEN}; }}

    /* Dashboard summary cards */
    [data-testid="stMetric"] {{
        background-color: #ffffff;
        border: 1px solid #e2ece2;
        border-left: 6px solid {MAIN_GREEN};
        border-radius: 8px;            /* 8px radius, never pill */
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }}

    /* Green buttons with 8px radius */
    .stButton>button, .stFormSubmitButton>button {{
        background-color: {MAIN_GREEN};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{
        background-color: {DARK_GREEN};
        color: {BRIGHT_YELLOW};
    }}

    /* Green sidebar with white text */
    [data-testid="stSidebar"] {{ background-color: {MAIN_GREEN}; }}
    [data-testid="stSidebar"] * {{ color: #ffffff; }}
</style>
""", unsafe_allow_html=True)


# ---- 4. DROPDOWN OPTION LISTS ------------------------------------------------
# These match the academy's real markets and courses so data stays clean.
COUNTRIES = ["United Kingdom", "USA", "UAE", "Canada", "Australia",
             "Germany", "Pakistan", "Saudi Arabia", "Other"]

COURSES = ["Basic / Madani Qaida", "Quran Reading", "Quran with Tajweed",
           "Quran Memorization (Hifz)", "Quran Translation",
           "Islamic Studies for Kids", "Duas and Kalimas",
           "English Language", "Urdu Language"]

CURRENCIES = ["GBP", "USD", "AED", "CAD", "AUD", "EUR", "PKR", "SAR"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SHIFTS = ["Morning", "Afternoon", "Evening", "Night"]

PAYMENT_METHODS = ["Bank Transfer", "PayPal", "Wise", "Card", "Cash", "Other"]

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


# =============================================================================
# 5. DATABASE SECTION
# -----------------------------------------------------------------------------
# We use a single SQLite file called "madani_academy.db".
# It is created automatically the first time you run the app.
# =============================================================================
DB_NAME = "madani_academy.db"


def get_connection():
    """Open a fresh connection to the database file."""
    # check_same_thread=False keeps Streamlit happy when it re-runs the script.
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    """Create the three tables if they do not already exist."""
    conn = get_connection()
    c = conn.cursor()

    # --- students table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name     TEXT NOT NULL,
            parent_name      TEXT,
            country          TEXT,
            whatsapp_number  TEXT,
            course           TEXT,
            teacher_name     TEXT,
            class_days       TEXT,
            class_time       TEXT,
            monthly_fee      REAL,
            currency         TEXT,
            payment_status   TEXT,
            start_date       TEXT,
            active_status    TEXT
        )
    """)

    # --- teachers table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name  TEXT NOT NULL,
            subject       TEXT,
            shift         TEXT,
            salary        REAL,
            status        TEXT
        )
    """)

    # --- fees table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            fee_id            INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id        INTEGER,
            student_name      TEXT,
            month             TEXT,
            fee_amount        REAL,
            currency          TEXT,
            payment_status    TEXT,
            payment_method    TEXT,
            payment_reference TEXT,
            payment_date      TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---- Student database helpers ----
def add_student(values):
    conn = get_connection()
    conn.execute("""
        INSERT INTO students
        (student_name, parent_name, country, whatsapp_number, course,
         teacher_name, class_days, class_time, monthly_fee, currency,
         payment_status, start_date, active_status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, values)
    conn.commit()
    conn.close()


def get_all_students():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM students ORDER BY student_id DESC", conn)
    conn.close()
    return df


def search_students(keyword):
    conn = get_connection()
    like = f"%{keyword}%"
    df = pd.read_sql_query("""
        SELECT * FROM students
        WHERE student_name    LIKE ?
           OR country         LIKE ?
           OR course          LIKE ?
           OR teacher_name    LIKE ?
           OR whatsapp_number LIKE ?
        ORDER BY student_id DESC
    """, conn, params=(like, like, like, like, like))
    conn.close()
    return df


def update_student(student_id, values):
    conn = get_connection()
    conn.execute("""
        UPDATE students SET
            student_name=?, parent_name=?, country=?, whatsapp_number=?,
            course=?, teacher_name=?, class_days=?, class_time=?,
            monthly_fee=?, currency=?, payment_status=?, start_date=?,
            active_status=?
        WHERE student_id=?
    """, (*values, student_id))
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    conn.commit()
    conn.close()


# ---- Teacher database helpers ----
def add_teacher(values):
    conn = get_connection()
    conn.execute("""
        INSERT INTO teachers (teacher_name, subject, shift, salary, status)
        VALUES (?,?,?,?,?)
    """, values)
    conn.commit()
    conn.close()


def get_all_teachers():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM teachers ORDER BY teacher_id DESC", conn)
    conn.close()
    return df


# ---- Fee database helpers ----
def add_fee(values):
    conn = get_connection()
    conn.execute("""
        INSERT INTO fees
        (student_id, student_name, month, fee_amount, currency,
         payment_status, payment_method, payment_reference, payment_date)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, values)
    conn.commit()
    conn.close()


def get_fees_by_status(status):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM fees WHERE payment_status=? ORDER BY fee_id DESC",
        conn, params=(status,))
    conn.close()
    return df


def get_all_fees():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM fees ORDER BY fee_id DESC", conn)
    conn.close()
    return df


# ---- Small helper functions ----
def prettify(df):
    """Make column names look nice for display (student_name -> Student Name)."""
    return df.rename(columns=lambda col: col.replace("_", " ").title())


def safe_index(options_list, value):
    """Return the position of `value` in a list, or 0 if not found.
    Used to pre-fill dropdowns when editing a record."""
    try:
        return options_list.index(value)
    except (ValueError, AttributeError):
        return 0


def parse_date(value):
    """Turn a stored text date back into a real date (fallback = today)."""
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return date.today()


# Create the tables (safe to call every time the app runs).
init_db()


# =============================================================================
# 6. PAGE: DASHBOARD
# =============================================================================
def page_dashboard():
    st.title("🕌 Madani Islamic Academy® Ltd")
    # Islamic greeting stays in Arabic script (brand rule).
    st.subheader("اَلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ")
    st.markdown("#### Dashboard")

    students_df = get_all_students()
    teachers_df = get_all_teachers()
    fees_df = get_all_fees()

    # --- Calculate the numbers for the cards ---
    total_students = len(students_df)
    total_teachers = len(teachers_df)

    # Monthly fee = sum of fees for ACTIVE students only.
    if not students_df.empty:
        active_df = students_df[students_df["active_status"] == "Active"]
        total_monthly_fee = active_df["monthly_fee"].sum()
    else:
        active_df = students_df
        total_monthly_fee = 0

    # Pending fee = sum of fee amounts marked as "Pending" in the fees table.
    if not fees_df.empty:
        total_pending = fees_df[fees_df["payment_status"] == "Pending"]["fee_amount"].sum()
    else:
        total_pending = 0

    # --- Show the four summary cards side by side ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total_students)
    c2.metric("Total Teachers", total_teachers)
    c3.metric("Total Monthly Fee", f"{total_monthly_fee:,.0f}")
    c4.metric("Pending Fees", f"{total_pending:,.0f}")

    # Because students pay in different currencies, adding them into one number
    # is only a rough total. Show a proper breakdown by currency underneath.
    if not active_df.empty:
        by_currency = active_df.groupby("currency")["monthly_fee"].sum()
        breakdown = "  ·  ".join(f"{cur} {amt:,.0f}" for cur, amt in by_currency.items())
        st.caption(f"Monthly fee by currency (active students):  {breakdown}")

    st.divider()

    # --- Charts ---
    col_left, col_right = st.columns(2)

    # Chart 1: how many students in each country (bar chart)
    with col_left:
        st.markdown("##### Students by Country")
        if not students_df.empty:
            country_counts = students_df["country"].value_counts().reset_index()
            country_counts.columns = ["Country", "Students"]
            fig = px.bar(country_counts, x="Country", y="Students",
                         color_discrete_sequence=[MAIN_GREEN])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add some students to see this chart.")

    # Chart 2: paid vs pending students (pie chart)
    with col_right:
        st.markdown("##### Payment Status")
        if not students_df.empty:
            status_counts = students_df["payment_status"].value_counts().reset_index()
            status_counts.columns = ["Payment Status", "Count"]
            fig2 = px.pie(status_counts, names="Payment Status", values="Count",
                          color="Payment Status",
                          color_discrete_map={"Paid": MAIN_GREEN,
                                              "Pending": BRIGHT_YELLOW})
            fig2.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Add some students to see this chart.")


# =============================================================================
# 7. PAGE: STUDENTS  (Add / View & Search / Edit / Delete)
# =============================================================================
def page_students():
    st.title("👨‍🎓 Students")

    # Four tabs across the top of the page.
    tab_add, tab_view, tab_edit, tab_delete = st.tabs(
        ["➕ Add Student", "📋 View & Search", "✏️ Edit Student", "🗑️ Delete Student"]
    )

    # ---------- ADD STUDENT ----------
    with tab_add:
        st.subheader("Add a new student")
        with st.form("add_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.text_input("Student Name *")
                parent_name  = st.text_input("Parent Name")
                country      = st.selectbox("Country", COUNTRIES)
                whatsapp     = st.text_input("WhatsApp Number", placeholder="+44 7480 676283")
                course       = st.selectbox("Course", COURSES)
                teacher_name = st.text_input("Teacher Name")
            with col2:
                class_days     = st.multiselect("Class Days", DAYS,
                                                default=["Monday", "Wednesday", "Friday"])
                class_time     = st.text_input("Class Time", placeholder="e.g. 5:00 PM (UK)")
                monthly_fee    = st.number_input("Monthly Fee", min_value=0.0, step=5.0)
                currency       = st.selectbox("Currency", CURRENCIES)
                payment_status = st.selectbox("Payment Status", ["Pending", "Paid"])
                start_date     = st.date_input("Start Date", value=date.today())
                active_status  = st.selectbox("Active Status", ["Active", "Inactive"])

            submitted = st.form_submit_button("➕ Add Student")
            if submitted:
                if student_name.strip() == "":
                    st.error("Student Name is required.")
                else:
                    add_student((
                        student_name.strip(), parent_name, country, whatsapp,
                        course, teacher_name, ", ".join(class_days), class_time,
                        monthly_fee, currency, payment_status,
                        str(start_date), active_status
                    ))
                    st.success(f"✅ Student '{student_name}' added successfully!")

    # ---------- VIEW & SEARCH ----------
    with tab_view:
        st.subheader("All students")
        keyword = st.text_input("🔍 Search by name, country, course, teacher or WhatsApp")
        df = search_students(keyword.strip()) if keyword.strip() else get_all_students()

        st.write(f"Showing **{len(df)}** student(s).")
        if df.empty:
            st.info("No students found. Add one from the 'Add Student' tab.")
        else:
            st.dataframe(prettify(df), use_container_width=True, hide_index=True)

    # ---------- EDIT STUDENT ----------
    with tab_edit:
        st.subheader("Edit an existing student")
        df = get_all_students()
        if df.empty:
            st.info("No students to edit yet.")
        else:
            # Build a dropdown like "12 - Ahmed Ali"
            options = {f"{row.student_id} - {row.student_name}": row.student_id
                       for row in df.itertuples()}
            choice = st.selectbox("Select a student", list(options.keys()))
            sid = options[choice]
            s = df[df["student_id"] == sid].iloc[0]   # the selected student's row

            # Turn stored "Mon, Wed" text back into a list for the multiselect
            current_days = [d.strip() for d in str(s["class_days"]).split(",") if d.strip() in DAYS]

            with st.form("edit_student_form"):
                col1, col2 = st.columns(2)
                with col1:
                    student_name = st.text_input("Student Name *", value=s["student_name"])
                    parent_name  = st.text_input("Parent Name", value=s["parent_name"] or "")
                    country      = st.selectbox("Country", COUNTRIES,
                                                index=safe_index(COUNTRIES, s["country"]))
                    whatsapp     = st.text_input("WhatsApp Number", value=s["whatsapp_number"] or "")
                    course       = st.selectbox("Course", COURSES,
                                                index=safe_index(COURSES, s["course"]))
                    teacher_name = st.text_input("Teacher Name", value=s["teacher_name"] or "")
                with col2:
                    class_days     = st.multiselect("Class Days", DAYS, default=current_days)
                    class_time     = st.text_input("Class Time", value=s["class_time"] or "")
                    monthly_fee    = st.number_input("Monthly Fee", min_value=0.0, step=5.0,
                                                     value=float(s["monthly_fee"] or 0))
                    currency       = st.selectbox("Currency", CURRENCIES,
                                                  index=safe_index(CURRENCIES, s["currency"]))
                    payment_status = st.selectbox("Payment Status", ["Pending", "Paid"],
                                                  index=safe_index(["Pending", "Paid"], s["payment_status"]))
                    start_date     = st.date_input("Start Date", value=parse_date(s["start_date"]))
                    active_status  = st.selectbox("Active Status", ["Active", "Inactive"],
                                                  index=safe_index(["Active", "Inactive"], s["active_status"]))

                saved = st.form_submit_button("💾 Save Changes")
                if saved:
                    if student_name.strip() == "":
                        st.error("Student Name is required.")
                    else:
                        update_student(sid, (
                            student_name.strip(), parent_name, country, whatsapp,
                            course, teacher_name, ", ".join(class_days), class_time,
                            monthly_fee, currency, payment_status,
                            str(start_date), active_status
                        ))
                        st.success("✅ Changes saved. Switch tabs or refresh to see the update.")

    # ---------- DELETE STUDENT ----------
    with tab_delete:
        st.subheader("Delete a student")
        df = get_all_students()
        if df.empty:
            st.info("No students to delete yet.")
        else:
            options = {f"{row.student_id} - {row.student_name}": row.student_id
                       for row in df.itertuples()}
            choice = st.selectbox("Select a student to delete", list(options.keys()))
            sid = options[choice]
            s = df[df["student_id"] == sid]

            st.warning("Please review the details below before deleting.")
            st.dataframe(prettify(s), use_container_width=True, hide_index=True)

            # Extra safety: a confirmation tick is required before deleting.
            confirm = st.checkbox("Yes, I confirm I want to permanently delete this student.")
            if st.button("🗑️ Delete Student"):
                if confirm:
                    delete_student(sid)
                    st.success("✅ Student deleted. Switch tabs or refresh to see the update.")
                else:
                    st.error("Please tick the confirmation box first.")


# =============================================================================
# 8. PAGE: TEACHERS  (Add / View)
# =============================================================================
def page_teachers():
    st.title("👩‍🏫 Teachers")

    tab_add, tab_view = st.tabs(["➕ Add Teacher", "📋 View Teachers"])

    # ---------- ADD TEACHER ----------
    with tab_add:
        st.subheader("Add a new teacher")
        with st.form("add_teacher_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                teacher_name = st.text_input("Teacher Name *")
                subject      = st.selectbox("Subject", COURSES + ["Other"])
                shift        = st.selectbox("Shift", SHIFTS)
            with col2:
                salary       = st.number_input("Salary", min_value=0.0, step=50.0)
                status       = st.selectbox("Status", ["Active", "Inactive"])

            submitted = st.form_submit_button("➕ Add Teacher")
            if submitted:
                if teacher_name.strip() == "":
                    st.error("Teacher Name is required.")
                else:
                    add_teacher((teacher_name.strip(), subject, shift, salary, status))
                    st.success(f"✅ Teacher '{teacher_name}' added successfully!")

    # ---------- VIEW TEACHERS ----------
    with tab_view:
        st.subheader("All teachers")
        df = get_all_teachers()
        st.write(f"Showing **{len(df)}** teacher(s).")
        if df.empty:
            st.info("No teachers yet. Add one from the 'Add Teacher' tab.")
        else:
            st.dataframe(prettify(df), use_container_width=True, hide_index=True)


# =============================================================================
# 9. PAGE: FEES  (Add record / View paid / View pending)
# =============================================================================
def page_fees():
    st.title("💰 Fees")

    tab_add, tab_paid, tab_pending = st.tabs(
        ["➕ Add Fee Record", "✅ Paid Fees", "⏳ Pending Fees"]
    )

    # ---------- ADD FEE RECORD ----------
    with tab_add:
        st.subheader("Add a fee record")
        students_df = get_all_students()

        if students_df.empty:
            st.info("Add a student first, then you can record their fees here.")
        else:
            # Pick the student from a dropdown (prevents typing mistakes).
            student_map = {
                f"{row.student_id} - {row.student_name}":
                    (row.student_id, row.student_name, row.monthly_fee, row.currency)
                for row in students_df.itertuples()
            }
            picked = st.selectbox("Student", list(student_map.keys()))
            sid, sname, s_fee, s_currency = student_map[picked]

            with st.form("add_fee_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    month_name = st.selectbox("Month", MONTHS, index=date.today().month - 1)
                    year       = st.number_input("Year", min_value=2020, max_value=2100,
                                                 value=date.today().year, step=1)
                    # Pre-fill the amount and currency from the student's record.
                    fee_amount = st.number_input("Fee Amount", min_value=0.0, step=5.0,
                                                 value=float(s_fee or 0))
                    currency   = st.selectbox("Currency", CURRENCIES,
                                              index=safe_index(CURRENCIES, s_currency))
                with col2:
                    payment_status    = st.selectbox("Payment Status", ["Pending", "Paid"])
                    payment_method    = st.selectbox("Payment Method", PAYMENT_METHODS)
                    payment_reference = st.text_input("Payment Reference",
                                                      placeholder="e.g. transaction ID")
                    payment_date      = st.date_input("Payment Date", value=date.today())

                submitted = st.form_submit_button("➕ Add Fee Record")
                if submitted:
                    month_str = f"{month_name} {int(year)}"
                    add_fee((
                        sid, sname, month_str, fee_amount, currency,
                        payment_status, payment_method, payment_reference,
                        str(payment_date)
                    ))
                    st.success(f"✅ Fee record for '{sname}' ({month_str}) added successfully!")

    # ---------- PAID FEES ----------
    with tab_paid:
        st.subheader("Paid fees")
        df = get_fees_by_status("Paid")
        st.write(f"Showing **{len(df)}** paid record(s).")
        if df.empty:
            st.info("No paid fee records yet.")
        else:
            st.dataframe(prettify(df), use_container_width=True, hide_index=True)

    # ---------- PENDING FEES ----------
    with tab_pending:
        st.subheader("Pending fees")
        df = get_fees_by_status("Pending")
        st.write(f"Showing **{len(df)}** pending record(s).")
        if df.empty:
            st.info("No pending fee records. 🎉")
        else:
            st.dataframe(prettify(df), use_container_width=True, hide_index=True)


# =============================================================================
# 10. SIDEBAR NAVIGATION + PAGE ROUTER
# -----------------------------------------------------------------------------
# The sidebar lets you switch between the four pages.
# =============================================================================
with st.sidebar:
    st.markdown("## 🕌 Madani Islamic Academy")
    st.caption("Management System")
    st.divider()
    page = st.radio(
        "Go to",
        ["📊 Dashboard", "👨‍🎓 Students", "👩‍🏫 Teachers", "💰 Fees"],
        label_visibility="collapsed",
    )

# Show the page the user picked.
if page == "📊 Dashboard":
    page_dashboard()
elif page == "👨‍🎓 Students":
    page_students()
elif page == "👩‍🏫 Teachers":
    page_teachers()
elif page == "💰 Fees":
    page_fees()
