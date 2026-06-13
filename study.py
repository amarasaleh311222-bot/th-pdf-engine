import streamlit as st
import pypdf
from google import genai

st.set_page_config(page_title="Local PDF AI Assistant", layout="wide")
st.title("📚 Local PDF AI Assistant (Powered by Gemini)")
st.subheader("Upload your study material to get started.")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.success(f"Successfully loaded: {uploaded_file.name}")

    # FIX: Changed to cache_data so it never re-reads the PDF text on button clicks!
    @st.cache_data
    def extract_text_from_pdf(file_bytes):
        pdf_reader = pypdf.PdfReader(file_bytes)
        full_text = ""
        # Keep it to a safe, highly-optimized page limit for speed
        max_pages = min(20, len(pdf_reader.pages))
        for i in range(max_pages):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                full_text += page_text + "\n"
        return full_text

    # Read the file data once and lock it into memory
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
            preset_query = "Based on this text, generate 5 study flashcards. Format them clearly as 'Front (Question):' and 'Back of Card (Answer):'."

    st.write("### 💬 Ask Anything")
    user_query = st.text_input("Enter your question or use a quick prompt above:", value=preset_query)

    if user_query:
        with st.spinner("Gemini is analyzing your document instantly..."):
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # Take a perfectly sized chunk of the document text for high speed response
                context = document_text[:8000]
                
                full_prompt = f"Context from PDF:\n{context}\n\nQuestion: {user_query}\n\nAnswer:"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                )
                
                st.write("### 🤖 Gemini Response:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Gemini API Error: {e}. Make sure your API key is correctly pasted!")
else:
    st.info("Please upload a PDF file from the sidebar to begin processing.")
