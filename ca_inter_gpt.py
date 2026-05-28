import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import os

# 1. Page Setup
st.set_page_config(page_title="CA Inter - GPT", layout="centered")
st.title("CA Inter - GPT")
st.caption("Updated for Sept 2026 & Jan 2027 (Finance Act 2025)")

# # 2. API Configuration (Smart Cloud + Local Fallback)
try:
    # This works when deployed live on Streamlit Cloud
    API_KEY = st.secrets["API_KEY"]

genai.configure(api_key=API_KEY)
# --- ADMIN AMENDMENT DATA LOADER ---
@st.cache_data
def load_inbuilt_amendments():
    amendments_text = ""
    folder_path = "amendments"
    
    # Silently read PDFs if the admin created the folder
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith('.pdf'):
                try:
                    file_path = os.path.join(folder_path, file_name)
                    with open(file_path, "rb") as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                amendments_text += text + "\n"
                except Exception:
                    pass
    return amendments_text

INBUILT_DATA = load_inbuilt_amendments()
# -----------------------------------

# 3. The Brain of the Operations 
SYSTEM_PROMPT = f"""
You are an elite, highly intelligent GPT specifically engineered for the CA Intermediate September 2026 and January 2027 examinations.

CRITICAL DIRECT TAX RULES (FINANCE ACT 2025 / AY 2026-27):
You MUST strictly apply the following Default Tax Regime (Sec 115BAC) slabs for all computations. NEVER use the old 3-6 lakh slabs.
- Up to ₹4,00,000: Nil
- ₹4,00,001 to ₹8,00,000: 5%
- ₹8,00,001 to ₹12,00,000: 10%
- ₹12,00,001 to ₹16,00,000: 15%
- ₹16,00,001 to ₹20,00,000: 20%
- ₹20,00,001 to ₹24,00,000: 25%
- Above ₹24,00,000: 30%
- Standard Deduction for Salaried Employees: ₹75,000
- Section 87A Rebate: Up to ₹12,00,000 taxable income (Maximum rebate ₹60,000).

INBUILT KNOWLEDGE BASE (ADMIN SPECIFIED AMENDMENTS):
Use the following validated regulatory text to answer specific doubts on Corporate Law, GST, and Accounting Standards amendments. Prioritize this information:
{INBUILT_DATA}

When evaluating uploaded answer sheets:
1. Read the answers thoroughly and line by line.
2. Mark executed perfectly and flawlessly with ✅✅.
3. Mark wherever the answer is right with ✅.
4. Mark wherever the answer is wrong with ❌, and explain the mistake while providing tips to score full marks.
5. Answer all student doubts regarding Taxation, Law, Audit, and Costing with precise section numbers and ICAI terminology.
6. Provide a step-wise mark breakdown at the end of every evaluation.

CONVERSATION STYLE (STRICT):
- If the user simply says "Hello" or greets you, reply with a very brief, casual greeting (e.g., "Hello! Ready when you are.").
- DO NOT repeat your rules, instructions, or capabilities.
- DO NOT introduce yourself or your role. Keep it invisible.
- Save your detailed outputs exclusively for when an actual answer sheet or doubt is provided.
"""

# 4. Initialize the Model
@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        system_instruction=SYSTEM_PROMPT,
        tools=["code_execution"]
    )

model = load_model()

# 5. Chat Memory Initialization
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# 6. Display Chat History (With Custom Avatars)
for message in st.session_state.chat_session.history:
    role = "user" if message.role == "user" else "assistant"
    avatar_icon = " " if role == "user" else " "
    
    with st.chat_message(role):
        for part in message.parts:
            if part.text:
                st.markdown(part.text)

# 7. User Input 
if prompt := st.chat_input("Ask me...", accept_file="multiple", file_type=["png", "jpg", "jpeg", "pdf"]):
    
    user_text = prompt.text if prompt.text else ""
    uploaded_files = prompt["files"] if "files" in prompt else []
    
    # Custom User Avatar
    with st.chat_message("user"):
        if uploaded_files:
            # Loop through ALL uploaded files to display them
            for file in uploaded_files:
                file_ext = file.name.split('.')[-1].lower()
                if file_ext in ['png', 'jpg', 'jpeg']:
                    st.image(file, width=300)
                elif file_ext == 'pdf':
                    st.markdown(f"📄 **Uploaded PDF:** {file.name}")
        if user_text:
            st.markdown(user_text)

    # 8. AI Processing
    with st.chat_message("assistant"):
        with st.spinner("Working on it..."):
            try:
                contents = []
                if uploaded_files:
                    # Loop through ALL uploaded files to send them to the AI
                    for file in uploaded_files:
                        file_ext = file.name.split('.')[-1].lower()
                        
                        if file_ext == 'pdf':
                            contents.append({
                                "mime_type": "application/pdf",
                                "data": file.getvalue()
                            })
                        else:
                            img = Image.open(file)
                            contents.append(img)
                
                if user_text:
                    contents.append(user_text)
                
                if not contents:
                    st.warning("Please type a message or upload an image/PDF.")
                    st.stop()

                response = st.session_state.chat_session.send_message(contents)
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")
