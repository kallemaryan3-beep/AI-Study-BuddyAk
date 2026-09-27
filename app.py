import streamlit as st
from google import genai
from pypdf import PdfReader
import sqlite3
import time

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

# =========================
# DATABASE
# =========================

def setup_database():
    conn = sqlite3.connect("visits.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_visit(name):
    conn = sqlite3.connect("visits.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO visits (name) VALUES (?)",
        (name,)
    )

    conn.commit()
    conn.close()


def get_visits():
    conn = sqlite3.connect("visits.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM visits")
    result = cursor.fetchone()[0]

    conn.close()

    return result


setup_database()

# =========================
# SIMPLE LOGIN
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


if not st.session_state.logged_in:

    st.title("📚 AI Study Buddy")

    st.write("### 🔐 Login")

    name = st.text_input(
        "Enter your name"
    )

    if st.button("Login"):

        if name.strip():

            st.session_state.logged_in = True
            st.session_state.username = name.strip()

            add_visit(name.strip())

            st.rerun()

        else:

            st.warning(
                "Please enter your name."
            )

    st.stop()


# =========================
# SIDEBAR
# =========================

st.sidebar.title("📚 AI Study Buddy")

st.sidebar.write(
    f"👋 Hello, {st.session_state.username}!"
)

st.sidebar.metric(
    "Total Visits",
    get_visits()
)

if st.sidebar.button("Log Out"):

    st.session_state.logged_in = False
    st.session_state.username = ""

    st.rerun()


# =========================
# GEMINI
# =========================

try:
    api_key = st.secrets["GEMINI_API_KEY"]

except Exception:

    st.error(
        "GEMINI_API_KEY is not configured in Streamlit Secrets."
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

            error_text = str(error)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):

                if attempt < 2:

                    time.sleep(2)

                    continue

            st.error(
                "Gemini error: " + error_text
            )

            return None

    return None


# =========================
# MAIN APP
# =========================

st.title("📚 AI Study Buddy")

st.write(
    "Upload your notes or PDF and let AI help you study."
)


# =========================
# SETTINGS
# =========================

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


# =========================
# PDF
# =========================

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

            text = page.extract_text()

            if text:
                notes += text + "\n"

    if not notes.strip():

        st.error(
            "I couldn't extract text from this PDF."
        )

        st.stop()

    notes = notes[:100000]

    st.success(
        "✅ Your notes are ready!"
    )


# =========================
# EXPLAIN NOTES
# =========================

if uploaded_file and mode == "Explain my notes":

    if st.button(
        "🧠 Explain My Notes"
    ):

        prompt = f"""
You are an expert tutor.

Explain these study notes clearly and simply.

Use:
- Simple language
- Important definitions
- Examples
- Key ideas
- A short summary

Only use information found in the study material.

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


# =========================
# FLASHCARDS
# =========================

elif uploaded_file and mode == "Make flashcards":

    if st.button(
        "🃏 Generate Flashcards"
    ):

        prompt = f"""
You are a study assistant.

Create useful flashcards from these notes.

Format them like:

### Card 1
**Question:** ...
**Answer:** ...

### Card 2
**Question:** ...
**Answer:** ...

Focus on important concepts.

Only use information from the notes.

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


# =========================
# QUIZ
# =========================

elif uploaded_file and mode == "Create a quiz":

    if st.button(
        "❓ Generate Quiz"
    ):

        prompt = f"""
You are an expert teacher.

Create a {num_questions}-question practice quiz
using ONLY the study material below.

Use a mixture of:
- Multiple choice
- True/false
- Short answer

Do not give the answer directly after each question.

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


# =========================
# STUDY GUIDE
# =========================

elif uploaded_file and mode == "Study guide":

    if st.button(
        "📖 Create Study Guide"
    ):

        prompt = f"""
You are an expert study coach.

Turn these notes into a clear study guide.

Include:

1. Main topics
2. Important vocabulary
3. Important facts
4. Concepts students commonly confuse
5. Examples
6. Things to memorize
7. Final review

Only use information supported by the notes.

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


# =========================
# ASK STUDY BUDDY
# =========================

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
            "📄 Upload a PDF first."
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


# =========================
# FOOTER
# =========================

st.divider()

st.caption(
    "📚 AI Study Buddy"
)
