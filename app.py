import streamlit as st
import pandas as pd
import os
from datetime import datetime
from google import genai

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

# ============================================================
# VISITOR DATABASE
# ============================================================

VISITOR_FILE = "visitors.csv"

if not os.path.exists(VISITOR_FILE):
    pd.DataFrame(
        columns=["Name", "Email", "Time"]
    ).to_csv(
        VISITOR_FILE,
        index=False
    )


def load_visitors():
    return pd.read_csv(VISITOR_FILE)


def save_visitor(name, email):

    visitors = load_visitors()

    new_visitor = pd.DataFrame({
        "Name": [name],
        "Email": [email],
        "Time": [
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ]
    })

    visitors = pd.concat(
        [visitors, new_visitor],
        ignore_index=True
    )

    visitors.to_csv(
        VISITOR_FILE,
        index=False
    )


# ============================================================
# LOGIN
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("📚 AI Study Buddy")

    st.subheader("Welcome!")

    name = st.text_input(
        "Your name"
    )

    email = st.text_input(
        "Your email"
    )

    if st.button("Continue"):

        if not name.strip():

            st.error(
                "Please enter your name."
            )

        elif not email.strip():

            st.error(
                "Please enter your email."
            )

        else:

            save_visitor(
                name.strip(),
                email.strip()
            )

            st.session_state.logged_in = True
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()

            st.rerun()

    st.stop()


# ============================================================
# GEMINI
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


def ask_gemini(prompt):

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    except Exception as error:

        st.error(
            "Gemini error: " + str(error)
        )

        return None


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📚 AI Study Buddy")

st.sidebar.write(
    "👤 " + st.session_state.name
)

st.sidebar.write(
    "📧 " + st.session_state.email
)

if st.sidebar.button("Log Out"):

    st.session_state.logged_in = False

    st.rerun()


# ============================================================
# STUDY BUDDY
# ============================================================

st.title("📚 AI Study Buddy")

st.write(
    "Upload your notes and let Gemini help you study."
)


uploaded_file = st.file_uploader(
    "📄 Upload a PDF",
    type=["pdf"]
)


notes = ""


if uploaded_file:

    from pypdf import PdfReader

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
        "✅ Notes loaded!"
    )


# ============================================================
# STUDY OPTIONS
# ============================================================

if uploaded_file:

    option = st.selectbox(
        "What would you like Gemini to do?",
        [
            "Explain my notes",
            "Make flashcards",
            "Create a quiz",
            "Create a study guide"
        ]
    )


    if option == "Explain my notes":

        if st.button(
            "🧠 Explain My Notes"
        ):

            prompt = f"""
You are an expert tutor.

Explain the following study material
clearly and simply.

Use:
- Simple language
- Important definitions
- Examples
- Key ideas
- A short summary

Only use information from the study material.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "Gemini is studying your notes..."
            ):

                answer = ask_gemini(
                    prompt
                )

            if answer:

                st.subheader(
                    "🧠 Explanation"
                )

                st.markdown(answer)


    elif option == "Make flashcards":

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
                "Gemini is creating flashcards..."
            ):

                answer = ask_gemini(
                    prompt
                )

            if answer:

                st.subheader(
                    "🃏 Flashcards"
                )

                st.markdown(answer)


    elif option == "Create a quiz":

        number = st.slider(
            "Number of questions",
            5,
            30,
            10
        )

        if st.button(
            "❓ Generate Quiz"
        ):

            prompt = f"""
You are an expert teacher.

Create a {number}-question practice quiz
using ONLY the following study material.

Use:
- Multiple choice
- True/false
- Short answer

After the questions, create an
ANSWER KEY section.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "Gemini is creating your quiz..."
            ):

                answer = ask_gemini(
                    prompt
                )

            if answer:

                st.subheader(
                    "❓ Practice Quiz"
                )

                st.markdown(answer)


    elif option == "Create a study guide":

        if st.button(
            "📖 Create Study Guide"
        ):

            prompt = f"""
You are an expert study coach.

Create a clear study guide from
the following study material.

Include:

1. Main topics
2. Important vocabulary
3. Important facts
4. Important concepts
5. Examples
6. Things to memorize
7. Final review

Only use information from the study material.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "Gemini is creating your study guide..."
            ):

                answer = ask_gemini(
                    prompt
                )

            if answer:

                st.subheader(
                    "📖 Study Guide"
                )

                st.markdown(answer)


# ============================================================
# ASK GEMINI
# ============================================================

st.divider()

st.subheader(
    "💬 Ask Your Study Buddy"
)

question = st.text_input(
    "Ask a question about your notes"
)


if question:

    if not notes:

        st.warning(
            "Please upload a PDF first."
        )

    else:

        prompt = f"""
You are a helpful AI tutor.

Answer the student's question using
ONLY the study material below.

If the answer is not in the material,
say that you cannot find it in the notes.

STUDY MATERIAL:

{notes}

QUESTION:

{question}
"""

        with st.spinner(
            "Gemini is thinking..."
        ):

            answer = ask_gemini(
                prompt
            )

        if answer:

            st.subheader(
                "🤖 Study Buddy"
            )

            st.markdown(answer)


# ============================================================
# VISITOR DASHBOARD
# ============================================================

st.divider()

with st.expander(
    "📊 Visitor Statistics"
):

    visitors = load_visitors()

    st.metric(
        "Total Visits",
        len(visitors)
    )

    if len(visitors) > 0:

        st.dataframe(
            visitors,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No visits yet."
        )
