
import os
import io
import base64
import fitz  # PyMuPDF
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ GOOGLE_API_KEY not found! Please set it in your .env file.")
else:
    genai.configure(api_key=API_KEY)

prompt_options = {
    "A - Alignment Check": "Evaluate how well the resume aligns with the job description. Highlight major matches and mismatches. Give a rating out of 5 and detailed feedback.",
    "B - Bullet Point Quality": "Analyze the clarity and impact of the resume's bullet points. Suggest improvements where necessary. Rate out of 5.",
    "C - Clarity & Conciseness": "Assess the overall clarity and conciseness of the resume. Identify areas that could be more to the point. Rate 1-5.",
    "D - Design & Format": "Review the visual layout, design, and formatting of the resume. Recommend changes for a more professional look. Rate 1-5.",
    "E - Experience Relevance": "Evaluate how relevant the candidate's experience is to the job description. Identify strong and weak areas. Rate 1-5.",
    "F - Formatting Consistency": "Check for consistent formatting in fonts, spacing, headers, etc. Point out inconsistencies. Rate 1-5.",
    "G - Grammar & Spelling": "Check for grammar, punctuation, and spelling errors. Provide corrections. Rate 1-5.",
    "H - Highlight Achievements": "Evaluate how well achievements are highlighted. Suggest improvements. Rate 1-5.",
    "I - Industry Keywords": "Check use of industry-relevant keywords. Suggest additions. Rate 1-5.",
    "J - Job History Gaps": "Identify any gaps in job history and suggest explanations. Rate 1-5.",
    "K - Key Skills Match": "Analyze how well key skills match job requirements. List missing or irrelevant skills. Rate 1-5.",
    "L - Length Appropriateness": "Evaluate if resume length is appropriate. Rate 1-5.",
    "M - Metrics & Numbers": "Check if resume uses metrics to quantify achievements. Suggest additions. Rate 1-5.",
    "N - Naming Conventions": "Check consistency in naming conventions (titles, degrees). Rate 1-5.",
    "O - Objective/ Summary Impact": "Critique the resume's objective or summary. Rate 1-5.",
    "P - Professional Tone": "Assess tone for professionalism and confidence. Rate 1-5.",
    "Q - Qualification Strength": "Evaluate strength of qualifications in context of job. Rate 1-5.",
    "R - Readability": "Analyze readability (font, spacing, layout). Rate 1-5.",
    "S - Soft Skills Evidence": "Look for evidence of soft skills. Rate 1-5.",
    "T - Tailoring for the Role": "Assess tailoring to role. Rate 1-5.",
    "U - Unnecessary Details": "Identify info that detracts from impact. Rate 1-5.",
    "V - Visual Hierarchy": "Evaluate visual hierarchy of sections. Rate 1-5.",
    "W - Work Experience Order": "Check if experience listed reverse chronologically. Rate 1-5.",
    "X - X-factor Elements": "Look for unique elements that set candidate apart. Rate 1-5.",
    "Y - Years of Experience Accuracy": "Verify years of experience match history. Rate 1-5.",
    "Z - Zero to Hero Plan": "If underqualified, outline a 6–12 month career strategy. Rate 1-5."
}

def input_pdf_setup(upload_file):
    try:
        upload_file.seek(0)
        pdf_bytes = upload_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        page = doc.load_page(0)  
        pix = page.get_pixmap()
        img_byte_arr = io.BytesIO()
        img_byte_arr.write(pix.tobytes("jpeg"))
        img_byte_arr.seek(0)

        return [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr.read()).decode()
        }]
    except Exception as e:
        st.error(f"❌ Failed to process PDF with PyMuPDF: {e}")
        return None

def get_gemini_response(input_text, pdf_content, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')  
        response = model.generate_content([input_text, pdf_content[0], prompt])
        return response.text
    except Exception as e:
        st.error(f"API call failed: {e}")
        return None

def extract_rating(response_text):
    import re
    if not response_text:
        return 0
    match = re.search(r'(\d(?:\.\d)?)\s*(?:/|out of)?\s*5', response_text)
    if match:
        try:
            return float(match.group(1))
        except:
            return 0
    return 0

st.set_page_config(page_title="🧠 ATS Resume Expert", layout="wide")
st.title("🧠 ATS Resume Evaluation System")

input_text = st.text_area("Enter the Job Description here:", height=150)
uploaded_file = st.file_uploader("Upload Your Resume (PDF only)", type=["pdf"])

if uploaded_file:
    st.success("PDF Uploaded Successfully!")

if st.button("Evaluate Resume"):
    if not API_KEY:
        st.warning("Please set your API key to proceed.")
    elif not input_text:
        st.warning("Please enter a Job Description.")
    elif not uploaded_file:
        st.warning("Please upload a resume PDF.")
    else:
        pdf_content = input_pdf_setup(uploaded_file)
        if pdf_content:
            with st.spinner("Analyzing resume with AI... This may take a minute."):
                all_responses = {}
                scores = []
                for key, prompt_text in prompt_options.items():
                    response = get_gemini_response(input_text, pdf_content, prompt_text)
                    all_responses[key] = response or "No response from AI."
                    rating = extract_rating(response)
                    scores.append(rating)

            st.subheader("📈 Overall Resume Score")
            max_score = 5 * len(prompt_options)
            total_score = sum(scores)
            st.metric(label="Score", value=f"{total_score:.1f} / {max_score}")

            st.subheader("📝 Detailed Resume Evaluation")

            for key, response in all_responses.items():
                with st.expander(key):
                    st.write(response)

            st.subheader("🎓 Recommended Certifications")
            cert_prompt = (
                "Based on the candidate's resume and the job description, "
                "recommend up to 5 relevant online certifications or courses that can enhance their qualifications. "
                "Each recommendation should include the name of the course, the platform (like Coursera, Udemy, edX, LinkedIn Learning), "
                "and a direct link (URL) to the course. Prefer free or highly rated options."
            )
            certs_response = get_gemini_response(input_text, pdf_content, cert_prompt)
            if certs_response:
                st.markdown(certs_response, unsafe_allow_html=True)
            else:
                st.write("No certification recommendations available.")


