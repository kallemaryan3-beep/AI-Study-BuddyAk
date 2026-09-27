import streamlit as st
from google import genai
from pypdf import PdfReader
import sqlite3
import time
from datetime import datetime

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

# ============================================================
# DATABASE
# ============================================================

DATABASE = "visits.db"


def setup_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            visit_time TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def record_visit(username):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO visits (username, visit_time)
        VALUES (?, ?)
        """,
        (username, current_time)
    )

    connection.commit()
    connection.close()


def get_total_visits():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM visits"
    )

    total = cursor.fetchone()[0]

    connection.close()

    return total


def get_user_visits(username):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM visits
        WHERE username = ?
        """,
        (username,)
    )

    total = cursor.fetchone()[0]

    connection.close()

    return total


def get_visitor_summary():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT username, COUNT(*) AS visits
        FROM visits
        GROUP BY username
        ORDER BY visits DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_visit_history():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT username, visit_time
        FROM visits
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


setup_database()


# ============================================================
# SIMPLE LOGIN
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


if not st.session_state.logged_in:

    st.title("📚 AI Study Buddy")

    st.write("### 🔐 Sign In")

    name = st.text_input(
        "Enter your name"
    )

    if st.button("Continue"):

        if name.strip():

            st.session_state.logged_in = True
            st.session_state.username = name.strip()

            st.rerun()

        else:

            st.warning(
                "Please enter your name."
            )

    st.stop()


# ============================================================
# RECORD VISIT
# ============================================================

if "visit_recorded" not in st.session_state:

    record_visit(
        st.session_state.username
    )

    st.session_state.visit_recorded = True


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📚 AI Study Buddy")

st.sidebar.write(
    f"👋 Hello, {st.session_state.username}!"
)

st.sidebar.divider()

st.sidebar.metric(
    "Your Visits",
    get_user_visits(
        st.session_state.username
    )
)

st.sidebar.metric(
    "Total Visits",
    get_total_visits()
)

st.sidebar.divider()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

st.sidebar.subheader("⚙️ Admin")

admin_password = st.sidebar.text_input(
    "Admin Password",
    type="password"
)

ADMIN_PASSWORD = "CHANGE_THIS_PASSWORD"


if admin_password == ADMIN_PASSWORD:

    show_admin = st.sidebar.checkbox(
        "📊 Open Admin Dashboard"
    )

else:

    show_admin = False


# ============================================================
# LOGOUT
# ============================================================

if st.sidebar.button("🚪 Log Out"):

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.visit_recorded = False

    st.rerun()


# ============================================================
# ADMIN PAGE
# ============================================================

if show_admin:

    st.title("📊 Visitor Dashboard")

    st.write(
        "Admin-only visitor statistics."
    )

    st.divider()

    total_visits = get_total_visits()

    visitor_summary = get_visitor_summary()

    visit_history = get_visit_history()

    # --------------------------------------------------------
    # TOP STATISTICS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Visits",
            total_visits
        )

    with col2:

        st.metric(
            "Unique Visitors",
            len(visitor_summary)
        )

    with col3:

        if visitor_summary:

            most_active = visitor_summary[0][0]

        else:

            most_active = "None"

        st.metric(
            "Most Visits",
            most_active
        )

    st.divider()

    # --------------------------------------------------------
    # VISITS BY USER
    # --------------------------------------------------------

    st.subheader(
        "👥 Visits by User"
    )

    if visitor_summary:

        for username, visits in visitor_summary:

            col1, col2 = st.columns(
                [3, 1]
            )

            with col1:

                st.write(
                    f"👤 {username}"
                )

            with col2:

                st.write(
                    f"**{visits} visits**"
                )

    else:

        st.info(
            "No visitors yet."
        )

    st.divider()

    # --------------------------------------------------------
    # VISIT HISTORY
    # --------------------------------------------------------

    st.subheader(
        "🕒 Visit History"
    )

    if visit_history:

        for username, visit_time in visit_history:

            st.write(
                f"👤 **{username}** — {visit_time}"
            )

    else:

        st.info(
            "No visit history yet."
        )

    st.divider()

    if st.button(
        "🔄 Refresh Dashboard"
    ):

        st.rerun()

    st.stop()


# ============================================================
# GEMINI
# ============================================================

try:

    api_key = st.secrets["GEMINI_API_KEY"]

except Exception:

    st.error(
        "GEMINI_API_KEY is not configured in Streamlit Secrets."
    )

    st.info(
        "Go to Streamlit Cloud → Manage app → Settings → Secrets."
    )

    st.stop()


client = genai.Client(
    api_key=api_key
)


def ask_ai(prompt):

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if response.text:

                return response.text

            return "Gemini returned an empty response."

        except Exception as error:

            error_message = str(error)

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            ):

                if attempt < 2:

                    time.sleep(2)

                    continue

            st.error(
                "Gemini error: " + error_message
            )

            return None

    return None


# ============================================================
# MAIN APP
# ============================================================

st.title("📚 AI Study Buddy")

st.write(
    "Upload your notes or PDF and let AI help you study."
)


# ============================================================
# STUDY SETTINGS
# ============================================================

st.sidebar.subheader(
    "Study Settings"
)

mode = st.sidebar.selectbox(
    "What do you want to do?",
    [
        "Explain my notes",
        "Make flashcards",
        "Create a quiz",
        "Study guide"
    ]
)

num_questions = st.sidebar.slider(
    "Number of quiz questions",
    min_value=5,
    max_value=30,
    value=10
)


# ============================================================
# PDF UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📄 Upload your notes or PDF",
    type=["pdf"]
)

notes = ""


if uploaded_file:

    with st.spinner(
        "📖 Reading your notes..."
    ):

        reader = PdfReader(
            uploaded_file
        )

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                notes += page_text + "\n"

    if not notes.strip():

        st.error(
            "I couldn't extract text from this PDF."
        )

        st.stop()

    notes = notes[:100000]

    st.success(
        "✅ Your notes are ready!"
    )


# ============================================================
# EXPLAIN
# ============================================================

if uploaded_file and mode == "Explain my notes":

    if st.button(
        "🧠 Explain My Notes"
    ):

        prompt = f"""
You are an expert tutor.

Explain the following study material clearly
and simply.

Use:

- Simple language
- Important definitions
- Examples
- Key ideas
- A short summary

Only use information supported by the study material.

STUDY MATERIAL:

{notes}
"""

        with st.spinner(
            "🧠 Creating explanation..."
        ):

            answer = ask_ai(prompt)

        if answer:

            st.subheader(
                "🧠 Explanation"
            )

            st.markdown(answer)


# ============================================================
# FLASHCARDS
# ============================================================

elif uploaded_file and mode == "Make flashcards":

    if st.button(
        "🃏 Generate Flashcards"
    ):

        prompt = f"""
You are a study assistant.

Create useful flashcards from the study material.

Format each card like:

### Card 1
**Question:** ...
**Answer:** ...

### Card 2
**Question:** ...
**Answer:** ...

Focus on important concepts.

Only use information supported by the study material.

STUDY MATERIAL:

{notes}
"""

        with st.spinner(
            "🃏 Creating flashcards..."
        ):

            answer = ask_ai(prompt)

        if answer:

            st.subheader(
                "🃏 Flashcards"
            )

            st.markdown(answer)


# ============================================================
# QUIZ
# ============================================================

elif uploaded_file and mode == "Create a quiz":

    if st.button(
        "❓ Generate Quiz"
    ):

        prompt = f"""
You are an expert teacher.

Create a {num_questions}-question practice quiz
based ONLY on the study material.

Use a mixture of:

- Multiple choice
- True/false
- Short answer

Do not provide answers immediately after
each question.

At the end create:

ANSWER KEY

Then provide the correct answers.

STUDY MATERIAL:

{notes}
"""

        with st.spinner(
            "❓ Creating quiz..."
        ):

            answer = ask_ai(prompt)

        if answer:

            st.subheader(
                "❓ Practice Quiz"
            )

            st.markdown(answer)


# ============================================================
# STUDY GUIDE
# ============================================================

elif uploaded_file and mode == "Study guide":

    if st.button(
        "📖 Create Study Guide"
    ):

        prompt = f"""
You are an expert study coach.

Turn the following material into a clear
study guide.

Include:

1. Main topics
2. Important vocabulary
3. Important facts
4. Concepts students commonly confuse
5. Examples
6. Things to memorize
7. Final review

Only use information supported by the study material.

STUDY MATERIAL:

{notes}
"""

        with st.spinner(
            "📖 Creating study guide..."
        ):

            answer = ask_ai(prompt)

        if answer:

            st.subheader(
                "📖 Study Guide"
            )

            st.markdown(answer)


# ============================================================
# ASK STUDY BUDDY
# ============================================================

st.divider()

st.subheader(
    "💬 Ask Your Study Buddy"
)

question = st.text_input(
    "Ask a question about your uploaded notes:"
)


if question:

    if not uploaded_file:

        st.warning(
            "📄 Please upload your notes or PDF first."
        )

    else:

        prompt = f"""
You are a helpful AI tutor.

Answer the student's question using ONLY
the study material below.

If the answer cannot be found in the material,
say that clearly instead of making something up.

STUDY MATERIAL:

{notes}

STUDENT QUESTION:

{question}
"""

        with st.spinner(
            "🤔 Thinking..."
        ):

            answer = ask_ai(prompt)

        if answer:

            st.subheader(
                "🤖 Study Buddy"
            )

            st.markdown(answer)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "📚 AI Study Buddy • Powered by Google Gemini"
)
