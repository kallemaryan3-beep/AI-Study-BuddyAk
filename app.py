import streamlit as st
import time
import sqlite3

from google import genai
from pypdf import PdfReader


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)


# ============================================================
# GOOGLE LOGIN
# ============================================================

if not st.user.is_logged_in:

    st.title("📚 AI Study Buddy")

    st.write("Please sign in with Google to use AI Study Buddy.")

    st.button(
        "🔐 Sign in with Google",
        on_click=st.login
    )

    st.stop()


# ============================================================
# USER INFORMATION
# ============================================================

user_name = st.user.get("name", "Student")
user_email = st.user.get("email", "")


# ============================================================
# VISIT DATABASE
# ============================================================

DATABASE = "visits.db"


def setup_database():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            visits INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()


def record_visit(email, name):
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        "SELECT visits FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    if user is None:

        cursor.execute(
            """
            INSERT INTO users (email, name, visits)
            VALUES (?, ?, ?)
            """,
            (email, name, 1)
        )

        visits = 1

    else:

        visits = user[0] + 1

        cursor.execute(
            """
            UPDATE users
            SET name = ?, visits = ?
            WHERE email = ?
            """,
            (name, visits, email)
        )

    connection.commit()
    connection.close()

    return visits


def get_total_visits():
    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(visits), 0) FROM users"
    )

    total = cursor.fetchone()[0]

    connection.close()

    return total


setup_database()


# ============================================================
# COUNT VISIT
# ============================================================

if "visit_recorded" not in st.session_state:

    my_visits = record_visit(
        user_email,
        user_name
    )

    st.session_state.visit_recorded = True
    st.session_state.my_visits = my_visits

else:

    my_visits = st.session_state.my_visits


total_visits = get_total_visits()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📚 AI Study Buddy")

st.sidebar.write(
    f"👋 Welcome, **{user_name}**"
)

st.sidebar.write(
    f"📧 {user_email}"
)

st.sidebar.divider()

st.sidebar.metric(
    "Your Visits",
    my_visits
)

st.sidebar.metric(
    "Total Visits",
    total_visits
)

st.sidebar.divider()

st.sidebar.button(
    "🚪 Sign Out",
    on_click=st.logout
)


# ============================================================
# GEMINI API
# ============================================================

try:

    api_key = st.secrets["GEMINI_API_KEY"]

except Exception:

    st.error(
        "GEMINI_API_KEY is missing from Streamlit Secrets."
    )

    st.stop()


client = genai.Client(
    api_key=api_key
)


# ============================================================
# MAIN APP
# ============================================================

st.title("📚 AI Study Buddy")

st.write(
    "Upload your notes or PDF and let AI help you study."
)


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(pdf_file):

    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ============================================================
# GEMINI FUNCTION
# ============================================================

def ask_ai(prompt):

    models = [
        "gemini-3.8-flash",
        "gemini-3.8-flash-lite"
    ]

    for model in models:

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if response.text:
                    return response.text

            except Exception as error:

                error_message = str(error)

                if (
                    "503" in error_message
                    or "UNAVAILABLE" in error_message
                ):

                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue

                break

    st.error(
        "Gemini is temporarily unavailable. "
        "Please wait a moment and try again."
    )

    return None


# ============================================================
# STUDY SETTINGS
# ============================================================

st.sidebar.subheader("Study Settings")

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

    with st.spinner("📖 Reading your notes..."):

        notes = extract_pdf_text(
            uploaded_file
        )

    if not notes.strip():

        st.error(
            "I couldn't extract text from this PDF."
        )

        st.stop()

    notes = notes[:100000]

    st.success(
        "✅ Your notes are ready!"
    )


    # ========================================================
    # EXPLAIN NOTES
    # ========================================================

    if mode == "Explain my notes":

        if st.button("🧠 Explain My Notes"):

            prompt = f"""
You are an expert tutor.

Explain the following study material clearly and simply.

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
                "🧠 Creating your explanation..."
            ):

                answer = ask_ai(prompt)

            if answer:

                st.subheader(
                    "🧠 Explanation"
                )

                st.markdown(answer)


    # ========================================================
    # FLASHCARDS
    # ========================================================

    elif mode == "Make flashcards":

        if st.button("🃏 Generate Flashcards"):

            prompt = f"""
You are a study assistant.

Create useful flashcards from the study material.

Format them like this:

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


    # ========================================================
    # QUIZ
    # ========================================================

    elif mode == "Create a quiz":

        if st.button("❓ Generate Quiz"):

            prompt = f"""
You are an expert teacher.

Create a {num_questions}-question practice quiz
based ONLY on the study material.

Use a mixture of:
- Multiple choice
- True/false
- Short answer

Do not give answers immediately after each question.

At the end, create:

ANSWER KEY

Then list the correct answers.

Only use information supported by the study material.

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


    # ========================================================
    # STUDY GUIDE
    # ========================================================

    elif mode == "Study guide":

        if st.button("📖 Create Study Guide"):

            prompt = f"""
You are an expert study coach.

Turn the study material into a clear study guide.

Include:

1. Main topics
2. Important vocabulary
3. Important facts
4. Concepts students commonly confuse
5. Examples
6. Things to memorize
7. Final review

Only use information supported by the material.

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

Answer the student's question using ONLY the
study material below.

If the answer cannot be found in the material,
say that clearly instead of making something up.

Give a clear and student-friendly explanation.

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

    st.markdown("### 🤖 Study Buddy")
    st.markdown(answer)
