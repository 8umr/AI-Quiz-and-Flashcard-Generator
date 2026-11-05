import streamlit as st
import json
import re
import os
import io
import pandas as pd
from openai import OpenAI

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Grok AI Quiz & Flashcard Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1D4ED8, #7C3AED, #DB2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .score-card {
        padding: 1.5rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        border: 1px solid #C7D2FE;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .score-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: #3730A3;
    }
    .question-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .flashcard {
        min-height: 220px;
        border-radius: 16px;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    .flashcard-front {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: #F8FAFC;
        border: 2px solid #475569;
    }
    .flashcard-back {
        background: linear-gradient(135deg, #0F766E 0%, #115E59 100%);
        color: #F0FDFA;
        border: 2px solid #14B8A6;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-easy { background-color: #DEF7EC; color: #03543F; }
    .badge-medium { background-color: #FEF08A; color: #713F12; }
    .badge-hard { background-color: #FDE8E8; color: #9B1C1C; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "flashcard_data" not in st.session_state:
    st.session_state.flashcard_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "flashcard_index" not in st.session_state:
    st.session_state.flashcard_index = 0
if "card_flipped" not in st.session_state:
    st.session_state.card_flipped = False
if "mastered_cards" not in st.session_state:
    st.session_state.mastered_cards = set()
if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""

# Sample notes for quick testing
SAMPLE_NOTES = """Cellular Respiration and Photosynthesis Overview:

1. Photosynthesis:
- Location: Occurs inside chloroplasts of plant cells.
- Light Reactions: Take place in the thylakoid membranes; water (H2O) is split to release oxygen (O2), generating ATP and NADPH.
- Calvin Cycle (Light-independent): Takes place in the stroma; utilizes CO2, ATP, and NADPH to produce glucose (G3P).
- Overall Equation: 6CO2 + 6H2O + Light Energy -> C6H12O6 + 6O2.
- Key Pigment: Chlorophyll a is the primary photosynthetic pigment, absorbing mainly blue-violet and red wavelengths.

2. Cellular Respiration:
- Purpose: Converts biochemical energy from nutrients into ATP, releasing waste products.
- Overall Equation: C6H12O6 + 6O2 -> 6CO2 + 6H2O + 36-38 ATP.
- Glycolysis: Occurs in the cytoplasm; breaks 1 glucose into 2 pyruvate molecules, yielding net 2 ATP and 2 NADH (anaerobic).
- Krebs Cycle (Citric Acid Cycle): Occurs in the mitochondrial matrix; yields 2 ATP, 6 NADH, and 2 FADH2 per glucose.
- Electron Transport Chain (ETC): Embedded in the inner mitochondrial membrane (cristae); uses oxygen as final electron acceptor to generate the majority of ATP via ATP synthase (oxidative phosphorylation).
- Anaerobic Alternative: In the absence of oxygen, fermentation occurs (lactic acid fermentation in animal muscle cells, alcoholic fermentation in yeast)."""

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Input
    env_api_key = os.environ.get("XAI_API_KEY", "")
    api_key = st.text_input(
        "xAI / Grok API Key",
        value=env_api_key,
        type="password",
        placeholder="xai-...",
        help="Get your API key from https://console.x.ai/"
    )
    
    if not api_key:
        st.warning("⚠️ Enter your Grok API key above to generate study materials.")
    else:
        st.success("API Key detected!")

    st.markdown("---")
    st.subheader("🛠️ Study Generation Settings")
    
    # Model Selection
    model_choice = st.selectbox(
        "Grok Model",
        options=["grok-2-latest", "grok-2-mini", "grok-beta"],
        index=0,
        help="Select the Grok model to generate your questions and explanations."
    )
    
    # Difficulty Selection
    difficulty = st.select_slider(
        "Quiz Difficulty Level",
        options=["Easy", "Medium", "Hard"],
        value="Medium",
        help="Easy: Direct recall. Medium: Conceptual understanding. Hard: Analytical reasoning & synthesis."
    )
    
    # Number of items
    num_questions = st.slider("Number of MCQs", min_value=3, max_value=10, value=5, step=1)
    num_flashcards = st.slider("Number of Flashcards", min_value=3, max_value=12, value=6, step=1)
    
    st.markdown("---")
    st.caption("💡 Tip: Use 'Load Sample Notes' to test the app without typing.")
    if st.button("📋 Load Sample Notes", use_container_width=True):
        st.session_state.notes_text = SAMPLE_NOTES
        st.rerun()

# ---------------------------------------------------------
# Helper Functions: Grok API Call & JSON Parsing
# ---------------------------------------------------------
def clean_json_text(raw_text: str) -> str:
    """Extract clean JSON content from code blocks or loose strings."""
    raw_text = raw_text.strip()
    # Remove markdown code block fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
    if match:
        return match.group(1).strip()
    return raw_text

def generate_study_material(api_key: str, model: str, notes: str, difficulty: str, n_quiz: int, n_flash: int):
    """Call Grok (xAI) OpenAI-compatible API to generate MCQs and flashcards."""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.xai.com/v1"
    )
    
    prompt = f"""
You are an expert educator and exam developer. Based on the lesson notes provided below, generate a high-quality study package consisting of:
1. Exactly {n_quiz} multiple-choice questions (MCQs) suited for {difficulty} difficulty.
2. Exactly {n_flash} flashcards covering the core definitions, formulas, or concepts.

### Difficulty Guidelines:
- Easy: Direct recall of definitions, dates, and primary facts.
- Medium: Application and understanding of key concepts, comparing mechanisms.
- Hard: Deep conceptual analysis, edge cases, synthesis, and distinguishing subtle differences between distractors.

### Lesson Notes:
\"\"\"
{notes}
\"\"\"

### Expected JSON Output Structure:
Respond ONLY with a valid JSON object. Do not include markdown preamble, chit-chat, or comments outside the JSON.
{{
  "quiz": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": [
        "A) Option one",
        "B) Option two",
        "C) Option three",
        "D) Option four"
      ],
      "correct_answer": "A",
      "explanation": "Detailed explanation of why A is correct and why other options are incorrect."
    }}
  ],
  "flashcards": [
    {{
      "id": 1,
      "front": "Concept or Question",
      "back": "Clear, concise definition or answer."
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional educational assessment AI. Always respond in strict, valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    
    raw_content = response.choices[0].message.content
    cleaned_json = clean_json_text(raw_content)
    return json.loads(cleaned_json)

# ---------------------------------------------------------
# Main UI Layout
# ---------------------------------------------------------
st.markdown('<div class="main-title">🎓 AI Quiz & Flashcard Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by Grok AI — Paste lesson notes, set your difficulty, practice MCQs with instant scoring, and master concepts with flashcards.</div>', unsafe_allow_html=True)

# Navigation Tabs
tab_input, tab_quiz, tab_flashcards, tab_export = st.tabs([
    "📝 1. Lesson Notes",
    "🎯 2. Practice Quiz",
    "🗂️ 3. Flashcards",
    "💾 4. Export & Study Pack"
])

# ---------------------------------------------------------
# Tab 1: Lesson Notes Input
# ---------------------------------------------------------
with tab_input:
    st.subheader("Paste Your Lesson Notes or Study Guide")
    
    user_notes = st.text_area(
        "Notes Content",
        value=st.session_state.notes_text,
        height=280,
        placeholder="Paste lecture transcripts, textbook chapters, summaries, or bullet points here..."
    )
    st.session_state.notes_text = user_notes
    
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        word_count = len(user_notes.split()) if user_notes.strip() else 0
        st.caption(f"📊 Word Count: **{word_count} words** | Selected Difficulty: **{difficulty}** | Generating **{num_questions} MCQs** & **{num_flashcards} Flashcards**")
    
    with col_btn:
        generate_clicked = st.button("🚀 Generate Quiz & Flashcards", type="primary", use_container_width=True)

    if generate_clicked:
        if not api_key:
            st.error("❌ Please provide a valid Grok API Key in the left sidebar.")
        elif not user_notes.strip():
            st.warning("⚠️ Please paste some lesson notes first, or click 'Load Sample Notes' in the sidebar.")
        else:
            with st.spinner(f"Grok ({model_choice}) is analyzing your notes and generating {difficulty} questions..."):
                try:
                    result = generate_study_material(
                        api_key=api_key,
                        model=model_choice,
                        notes=user_notes,
                        difficulty=difficulty,
                        n_quiz=num_questions,
                        n_flash=num_flashcards
                    )
                    
                    st.session_state.quiz_data = result.get("quiz", [])
                    st.session_state.flashcard_data = result.get("flashcards", [])
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.flashcard_index = 0
                    st.session_state.card_flipped = False
                    st.session_state.mastered_cards = set()
                    
                    st.success("🎉 Quiz & Flashcards generated successfully! Switch to the 'Practice Quiz' or 'Flashcards' tab above.")
                except Exception as e:
                    st.error(f"Failed to generate study materials: {str(e)}")

# ---------------------------------------------------------
# Tab 2: Interactive Quiz Mode
# ---------------------------------------------------------
with tab_quiz:
    if not st.session_state.quiz_data:
        st.info("👋 No quiz generated yet. Paste your lesson notes in Tab 1 and click 'Generate Quiz & Flashcards'.")
    else:
        st.subheader("Interactive Multiple-Choice Quiz")
        st.caption(f"Difficulty: **{difficulty}** | Total Questions: **{len(st.session_state.quiz_data)}**")
        
        # Display quiz questions
        for idx, q in enumerate(st.session_state.quiz_data):
            q_id = q.get("id", idx + 1)
            q_text = q.get("question", "")
            options = q.get("options", [])
            correct_letter = q.get("correct_answer", "").strip().upper()
            
            st.markdown(f"#### Question {idx + 1}")
            st.markdown(f"**{q_text}**")
            
            # Format radio choices cleanly
            radio_key = f"q_{idx}"
            selected = st.radio(
                f"Select answer for Question {idx + 1}:",
                options=options,
                index=options.index(st.session_state.user_answers[idx]) if idx in st.session_state.user_answers and st.session_state.user_answers[idx] in options else None,
                key=radio_key,
                disabled=st.session_state.quiz_submitted,
                label_visibility="collapsed"
            )
            if selected:
                st.session_state.user_answers[idx] = selected
            
            # Show review feedback if submitted
            if st.session_state.quiz_submitted:
                user_choice = st.session_state.user_answers.get(idx, "")
                user_letter = user_choice[0].upper() if user_choice else ""
                
                is_correct = (user_letter == correct_letter)
                if is_correct:
                    st.success(f"✅ **Correct!** Your answer: {user_choice}")
                else:
                    if user_choice:
                        st.error(f"❌ **Incorrect.** You selected: {user_choice} | Correct Answer: **Option {correct_letter}**")
                    else:
                        st.warning(f"⚠️ **Unanswered.** Correct Answer: **Option {correct_letter}**")
                
                with st.expander(f"💡 Explanation for Question {idx + 1}", expanded=not is_correct):
                    st.write(q.get("explanation", "No explanation provided."))
            
            st.markdown("---")
        
        # Submit & Reset Action Buttons
        col_submit, col_reset = st.columns([1, 1])
        with col_submit:
            if not st.session_state.quiz_submitted:
                if st.button("📝 Submit Quiz & View Score", type="primary", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
            else:
                if st.button("🔄 Retake Quiz", use_container_width=True):
                    st.session_state.quiz_submitted = False
                    st.session_state.user_answers = {}
                    st.rerun()
                    
        with col_reset:
            if st.button("🗑️ Clear Quiz Data", use_container_width=True):
                st.session_state.quiz_data = None
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

        # Scorecard Calculation
        if st.session_state.quiz_submitted:
            total_q = len(st.session_state.quiz_data)
            correct_count = 0
            for idx, q in enumerate(st.session_state.quiz_data):
                user_choice = st.session_state.user_answers.get(idx, "")
                user_letter = user_choice[0].upper() if user_choice else ""
                correct_letter = q.get("correct_answer", "").strip().upper()
                if user_letter == correct_letter:
                    correct_count += 1
            
            percentage = round((correct_count / total_q) * 100) if total_q > 0 else 0
            
            badge_msg = "Outstanding Mastery! 🏆" if percentage >= 80 else ("Good effort, review weak areas! 📚" if percentage >= 50 else "Keep practicing, review notes! 💪")
            
            st.markdown(f"""
            <div class="score-card">
                <div style="font-size: 1.1rem; color: #4338CA; font-weight: 600;">FINAL SCORE REPORT</div>
                <div class="score-number">{correct_count} / {total_q}</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #1E1B4B; margin-bottom: 0.5rem;">{percentage}%</div>
                <div style="font-size: 1rem; color: #4B5563;">{badge_msg}</div>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Tab 3: Interactive Flashcard Mode
# ---------------------------------------------------------
with tab_flashcards:
    if not st.session_state.flashcard_data:
        st.info("👋 No flashcards generated yet. Paste your lesson notes in Tab 1 and click 'Generate Quiz & Flashcards'.")
    else:
        st.subheader("Interactive Study Flashcards")
        
        cards = st.session_state.flashcard_data
        total_cards = len(cards)
        current_idx = st.session_state.flashcard_index
        card = cards[current_idx]
        
        # Progress Bar & Mastered Status
        mastered_count = len(st.session_state.mastered_cards)
        progress = (current_idx + 1) / total_cards
        st.progress(progress)
        
        col_meta1, col_meta2 = st.columns([1, 1])
        with col_meta1:
            st.write(f"Card **{current_idx + 1}** of **{total_cards}**")
        with col_meta2:
            st.write(f"Mastered: **{mastered_count} / {total_cards}** cards")
        
        # Flashcard Component
        is_flipped = st.session_state.card_flipped
        card_class = "flashcard-back" if is_flipped else "flashcard-front"
        side_label = "BACK — DEFINITION / ANSWER" if is_flipped else "FRONT — CONCEPT / QUESTION"
        content_text = card.get("back", "") if is_flipped else card.get("front", "")
        
        st.markdown(f"""
        <div class="flashcard {card_class}">
            <div style="font-size: 0.8rem; letter-spacing: 0.1em; opacity: 0.8; margin-bottom: 1rem;">
                {side_label}
            </div>
            <div style="font-size: 1.35rem; font-weight: 600; line-height: 1.6;">
                {content_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Flashcard Controls
        c1, c2, c3, c4 = st.columns([1, 1.2, 1, 1])
        
        with c1:
            if st.button("⬅️ Previous", disabled=(current_idx == 0), use_container_width=True):
                st.session_state.flashcard_index -= 1
                st.session_state.card_flipped = False
                st.rerun()
                
        with c2:
            flip_label = "🔄 Flip to Front" if is_flipped else "🔄 Flip to Back"
            if st.button(flip_label, type="primary", use_container_width=True):
                st.session_state.card_flipped = not st.session_state.card_flipped
                st.rerun()
                
        with c3:
            if current_idx in st.session_state.mastered_cards:
                if st.button("✅ Mastered", use_container_width=True):
                    st.session_state.mastered_cards.remove(current_idx)
                    st.rerun()
            else:
                if st.button("⭐ Mark Mastered", use_container_width=True):
                    st.session_state.mastered_cards.add(current_idx)
                    st.rerun()
                    
        with c4:
            if st.button("Next ➡️", disabled=(current_idx == total_cards - 1), use_container_width=True):
                st.session_state.flashcard_index += 1
                st.session_state.card_flipped = False
                st.rerun()
                
        st.markdown("---")
        with st.expander("👀 View All Flashcards in List / Table"):
            df_cards = pd.DataFrame(cards)[["front", "back"]]
            df_cards.columns = ["Front (Concept)", "Back (Explanation)"]
            st.dataframe(df_cards, use_container_width=True)

# ---------------------------------------------------------
# Tab 4: Export & Study Pack
# ---------------------------------------------------------
with tab_export:
    st.subheader("💾 Export Your Study Materials")
    st.caption("Download your generated quizzes and flashcards for offline review, printing, or Anki.")
    
    if not st.session_state.quiz_data and not st.session_state.flashcard_data:
        st.info("No study content generated yet. Create a quiz in Tab 1 to enable export.")
    else:
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        # 1. Export Quiz Markdown
        with col_exp1:
            st.markdown("#### 📄 Printable Quiz (Markdown)")
            quiz_md = "# Lesson Quiz & Study Guide\n\n"
            if st.session_state.quiz_data:
                for idx, q in enumerate(st.session_state.quiz_data):
                    quiz_md += f"### Question {idx + 1}\n{q.get('question')}\n\n"
                    for opt in q.get("options", []):
                        quiz_md += f"- {opt}\n"
                    quiz_md += f"\n**Correct Answer:** {q.get('correct_answer')}\n"
                    quiz_md += f"**Explanation:** {q.get('explanation')}\n\n---\n\n"
            
            st.download_button(
                label="📥 Download Quiz (.md)",
                data=quiz_md,
                file_name="lesson_quiz.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        # 2. Export Flashcards CSV (Anki compatible)
        with col_exp2:
            st.markdown("#### 🗃️ Anki / Quizlet CSV")
            if st.session_state.flashcard_data:
                csv_buffer = io.StringIO()
                df_export = pd.DataFrame(st.session_state.flashcard_data)[["front", "back"]]
                df_export.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Flashcards (.csv)",
                    data=csv_data,
                    file_name="flashcards_anki.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.caption("No flashcards to export.")
                
        # 3. Export Full JSON Study Pack
        with col_exp3:
            st.markdown("#### 📦 Complete Study Pack (JSON)")
            pack_data = {
                "quiz": st.session_state.quiz_data,
                "flashcards": st.session_state.flashcard_data
            }
            json_str = json.dumps(pack_data, indent=2)
            
            st.download_button(
                label="📥 Download Full Pack (.json)",
                data=json_str,
                file_name="study_pack.json",
                mime="application/json",
                use_container_width=True
            )
