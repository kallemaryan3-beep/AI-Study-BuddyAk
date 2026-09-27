import os
import io
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# -----------------------------
# Configuration
# -----------------------------

st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI Study Buddy")
st.write("Upload your notes or PDF and let AI help you study.")

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY is not configured.")
    st.stop()

client = OpenAI(api_key=api_key)


# -----------------------------
# Helper functions
# -----------------------------

def extract_pdf_text(pdf_file):
    """Extract text from an uploaded PDF."""
    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def ask_ai(prompt):
    """Send a prompt to the AI model."""
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text


# -----------------------------
# Sidebar
# -----------------------------

st.sidebar.header("Study Settings")

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


# -----------------------------
# Upload
# -----------------------------

uploaded_file = st.file_uploader(
    "📄 Upload your notes or PDF",
    type=["pdf"]
)


if uploaded_file:

    with st.spinner("Reading your notes..."):
        notes = extract_pdf_text(uploaded_file)

    if not notes.strip():
        st.error(
            "I couldn't extract text from this PDF. "
            "Try a text-based PDF instead."
        )
        st.stop()

    # Prevent extremely large prompts
    notes = notes[:100000]

    st.success("Your notes are ready!")

    # -------------------------
    # Explain
    # -------------------------

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
- A short summary at the end

Do not invent information that isn't supported by the material.

STUDY MATERIAL:

{notes}
"""

            with st.spinner("Creating your explanation..."):
                answer = ask_ai(prompt)

            st.subheader("🧠 Explanation")
            st.markdown(answer)

    # -------------------------
    # Flashcards
    # -------------------------

    elif mode == "Make flashcards":

        if st.button("🃏 Generate Flashcards"):

            prompt = f"""
You are a study assistant.

Create useful flashcards from the following study material.

Format every card like this:

### Card 1
**Question:** ...
**Answer:** ...

Make the questions test important concepts rather than tiny details.

STUDY MATERIAL:

{notes}
"""

            with st.spinner("Creating flashcards..."):
                answer = ask_ai(prompt)

            st.subheader("🃏 Flashcards")
            st.markdown(answer)

    # -------------------------
    # Quiz
    # -------------------------

    elif mode == "Create a quiz":

        if st.button("❓ Generate Quiz"):

            prompt = f"""
You are an expert teacher.

Create a {num_questions}-question practice quiz
based ONLY on the following study material.

Use a mixture of:
- Multiple choice
- True/false
- Short answer

Do NOT provide the answers immediately.

After the questions, create a section called:

ANSWER KEY

Put the correct answers there.

STUDY MATERIAL:

{notes}
"""

            with st.spinner("Creating your quiz..."):
                answer = ask_ai(prompt)

            st.subheader("❓ Practice Quiz")
            st.markdown(answer)

    # -------------------------
    # Study Guide
    # -------------------------

    elif mode == "Study guide":

        if st.button("📖 Create Study Guide"):

            prompt = f"""
You are an expert study coach.

Turn the following material into a clear study guide.

Include:

1. Main topics
2. Important vocabulary
3. Important facts
4. Concepts students commonly confuse
5. Examples
6. Things to memorize
7. A short final review

Only use information supported by the material.

STUDY MATERIAL:

{notes}
"""

            with st.spinner("Creating your study guide..."):
                answer = ask_ai(prompt)

            st.subheader("📖 Study Guide")
            st.markdown(answer)


# -----------------------------
# General AI Tutor
# -----------------------------

st.divider()

st.subheader("💬 Ask Your Study Buddy")

question = st.text_input(
    "Ask a question about your uploaded notes:"
)

if question and uploaded_file:

    prompt = f"""
You are a helpful AI tutor.

Answer the student's question using the study
material below.

If the answer cannot be found in the material,
say that clearly instead of making something up.

STUDY MATERIAL:
{notes}

STUDENT QUESTION:
{question}
"""

    with st.spinner("Thinking..."):
        answer = ask_ai(prompt)

    st.markdown("### 🤖 Study Buddy")
    st.markdown(answer)