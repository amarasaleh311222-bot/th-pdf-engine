import streamlit as st
import pypdf
import os
import re
from google import genai

# Read the key directly from Render's Environment Variables panel
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Fallback block if Render vault isn't matching perfectly
if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        st.error("API Key missing! Please add GEMINI_API_KEY to Render's Environment Variables.")

# Initialize session state variables so data doesn't disappear on click
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "normal_response" not in st.session_state:
    st.session_state.normal_response = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- SIDEBAR UPLOADER SECTION ---
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# --- MAIN APP CODES ---
if uploaded_file is not None:
    st.success(f"Successfully loaded: {uploaded_file.name}")

    @st.cache_data
    def extract_text_from_pdf(file_bytes):
        pdf_reader = pypdf.PdfReader(file_bytes)
        full_text = ""
        max_pages = min(20, len(pdf_reader.pages))
        for i in range(max_pages):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                full_text += page_text + "\n"
        return full_text

    document_text = extract_text_from_pdf(uploaded_file)

    st.write("### ⚡ Quick Study Tools")
    col1, col2, col3 = st.columns(3)
    
    preset_query = ""
    
    with col1:
        if st.button("📝 Generate Comprehensive Summary"):
            preset_query = "Provide a comprehensive, structured summary of the main themes and concepts discussed in this document."
    with col2:
        if st.button("🔑 Extract Key Points & Terms"):
            preset_query = "Extract a bulleted list of the most important key points, core definitions, and terms from this text."
    with col3:
        if st.button("🎴 Create Study Flashcards"):
            preset_query = "Based on this text, generate 5 study flashcards. You must strictly follow this exact format for each card:\n\n[CARD_START]\nFRONT: (Write the question here)\nBACK: (Write the answer here)\n[CARD_END]"

    st.write("### 💬 Ask Anything")
    user_query = st.text_input("Enter your question or use a quick prompt above:", value=preset_query)

    # Trigger API only if the user query changed or a button was pressed
    if user_query and user_query != st.session_state.last_query:
        st.session_state.last_query = user_query
        
        with st.spinner("Gemini is analyzing your document instantly..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                context = document_text[:8000]
                full_prompt = f"Context from PDF:\n{context}\n\nQuestion: {user_query}\n\nAnswer:"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                )
                
                raw_text = response.text
                
                # Check if we are running flashcards
                if "[CARD_START]" in user_query or "Flashcards" in user_query:
                    cards = re.findall(r'\[CARD_START\](.*?)\[CARD_END\]', raw_text, re.DOTALL)
                    parsed_cards = []
                    
                    for card in cards:
                        # Fixed: Bulletproof matching that stops at BACK regardless of spacing or line breaks
                        front_match = re.search(r'FRONT:\s*(.*?)\s*(?=BACK:|$)', card, re.IGNORECASE | re.DOTALL)
                        back_match = re.search(r'BACK:\s*(.*)', card, re.IGNORECASE | re.DOTALL)
                        
                        if front_match and back_match:
                            parsed_cards.append({
                                "front": front_match.group(1).strip(),
                                "back": back_match.group(1).strip()
                            })
                    
                    if parsed_cards:
                        st.session_state.flashcards = parsed_cards
                        st.session_state.normal_response = None
                    else:
                        st.session_state.normal_response = raw_text
                        st.session_state.flashcards = None
                else:
                    st.session_state.normal_response = raw_text
                    st.session_state.flashcards = None
                    
            except Exception as e:
                st.error(f"Gemini API Error: {e}")

    # --- RENDERING SECTION ---
    if st.session_state.flashcards or st.session_state.normal_response:
        st.write("### 🤖 Gemini Response:")

        if st.session_state.flashcards:
            for idx, card in enumerate(st.session_state.flashcards, 1):
                with st.container(border=True):
                    st.write(f"**🎴 Flashcard {idx}**")
                    
                    # Clean fallback check just in case text parsing encounters an issue
                    q_text = card['front'] if card['front'] else "Question content missing. Click below to flip."
                    st.write(f"**Question:** {q_text}")
                    
                    # Interactive Flip Checkbox
                    if st.checkbox("🔄 Flip to see Answer", key=f"card_{idx}"):
                        st.markdown("---")
                        ans_text = card['back'] if card['back'] else "Answer content missing."
                        st.write(f"**Answer:** {ans_text}")
                        
        elif st.session_state.normal_response:
            st.write(st.session_state.normal_response)
else:
    st.info("Please upload a PDF file from the sidebar to begin processing.")
