# 🎓 AI Quiz & Flashcard Generator (Powered by Grok API)

An interactive, AI-driven study tool built with **Streamlit** and the **xAI Grok API** (`grok-2-latest`, `grok-2-mini`, `grok-beta`). Students can paste lecture transcripts or study notes, choose difficulty levels (Easy, Medium, Hard), and automatically generate interactive multiple-choice questions (with explanations) and interactive flip flashcards.

## 🚀 Features

* **Grok AI Integration**: Uses the official xAI endpoint (`https://api.xai.com/v1`) via the OpenAI-compatible SDK.

* **Custom Difficulty**:

  * **Easy**: Direct recall of key definitions, dates, and core terms.

  * **Medium**: Conceptual understanding and comparison of mechanisms.

  * **Hard**: Synthesis, edge cases, and subtle distractor analysis.

* **Interactive MCQ Quiz**:

  * Live answering with instant or submit-and-grade options.

  * Full scorecard calculation with percentages and mastery badges.

  * In-depth pedagogical explanations for why the correct answer is right and why distractors are wrong.

  * Retake or reset quiz anytime.

* **Interactive Flashcards**:

  * Front-and-back flip cards with 3D gradient styling.

  * Mastery tracking ("Mark as Mastered") with live study progress bars.

  * Carousel navigation (Previous / Next) and complete overview table.

* **One-Click Export**:

  * Export printable quizzes as Markdown (`.md`).

  * Export flashcards as CSV (`.csv`) for import into **Anki** or **Quizlet**.

  * Export full study packs as JSON (`.json`).

* **Quick Test Sample**: Includes pre-loaded sample notes (Cellular Respiration & Photosynthesis) for immediate testing.

## 📦 Installation & Setup

### 1. Clone or Download Project Files

Ensure `app.py` and `requirements.txt` are in the same folder.

```
# Create a virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

```

### 2. Install Dependencies

```
pip install -r requirements.txt

```

### 3. Configure Your Grok API Key

You can provide your xAI Grok API key in one of two ways:

#### Option A: In the Streamlit Sidebar (Easiest)

Simply run the app, paste your API key (`xai-...`) into the sidebar password field, and start generating!

#### Option B: As an Environment Variable

Set the `XAI_API_KEY` environment variable in your terminal:

```
# On macOS/Linux:
export XAI_API_KEY="your-xai-api-key-here"

# On Windows (Command Prompt):
set XAI_API_KEY=your-xai-api-key-here

# On Windows (PowerShell):
$env:XAI_API_KEY="your-xai-api-key-here"

```

## 🏃 Running the Application

Launch the Streamlit app:

```
streamlit run app.py

```

The app will open automatically in your browser at `http://localhost:8501`.

## 📁 Project Structure

```
├── app.py              # Streamlit application with Grok integration
├── requirements.txt    # Python dependencies
└── README.md           # Documentation and setup instructions

```