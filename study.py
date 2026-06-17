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
    is_flashcard_mode = False
    
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

    if user_query:
        if "[CARD_START]" in user_query or "Flashcards" in user_query:
            is_flashcard_mode = True

        with st.spinner("Gemini is analyzing your document instantly..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                context = document_text[:8000]
                full_prompt = f"Context from PDF:\n{context}\n\nQuestion: {user_query}\n\nAnswer:"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                )
                
                st.write("### 🤖 Gemini Response:")
                
                if is_flashcard_mode:
                    raw_text = response.text
                    cards = re.findall(r'\[CARD_START\](.*?)\[CARD_END\]', raw_text, re.DOTALL)
                    
                    if cards:
                        for idx, card in enumerate(cards, 1):
                            front_match = re.search(r'FRONT:\s*(.*?)(?=\nBACK:|$)', card, re.DOTALL)
                            back_match = re.search(r'BACK:\s*(.*)', card, re.DOTALL)
                            
                            if front_match and back_match:
                                front_text = front_match.group(1).strip()
                                back_text = back_match.group(1).strip()
                                
                                with st.container(border=True):
                                    st.write(f"**🎴 Flashcard {idx}**")
                                    st.write(f"**Question:** {front_text}")
                                    
                                    # Interactive Reveal Checkbox
                                    if st.checkbox("🔄 Flip to see Answer", key=f"card_{idx}"):
                                        st.markdown("---")
                                        st.write(f"**Answer:** {back_text}")
                    else:
                        st.write(raw_text)
                else:
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"Gemini API Error: {e}")
else:
    st.info("Please upload a PDF file from the sidebar to begin processing.")
