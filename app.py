import os
import io

# (Optional) from dotenv import load_dotenv
# load_dotenv()

import openai
import streamlit as st
import PyPDF2  # For extracting text from PDF

# ------------------------------------------------------------------------------
# 1) Hardcoded API Key (Security Risk in Production)
#    Replace this with your valid API key or use environment variables.
# ------------------------------------------------------------------------------
openai.api_key = ""


# ------------------------------------------------------------------------------
# 2) Extract Text from PDF
# ------------------------------------------------------------------------------
def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from each page of the uploaded PDF using PyPDF2,
    then concatenates it into a single string.
    """
    if not uploaded_file:
        raise FileNotFoundError("No file uploaded.")

    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    all_text = []
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page_text = page.extract_text() or ""
        all_text.append(page_text)

    # Combine all pages
    pdf_text = "\n".join(all_text)

    # Truncate if too large to avoid hitting token limits
    max_chars = 8000
    if len(pdf_text) > max_chars:
        pdf_text = pdf_text[:max_chars] + "\n\n[...Content Truncated...]"
    return pdf_text

# ------------------------------------------------------------------------------
# 3) Get OpenAI Response
#    Tries "gpt-4o" first; if it fails, tries "gpt-4omini".
# ------------------------------------------------------------------------------
def get_openai_response(system_prompt, user_message):
    """
    Attempts to call gpt-4o first; if it fails, fallback to gpt-4omini.
    """
    models_to_try = ["gpt-4o", "gpt-4omini"]  # Change to models you actually have access to
    error_messages = []

    for model in models_to_try:
        try:
            # Old ChatCompletion call works in openai==0.28.0
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_tokens=2000,
                temperature=0.1 
            )
            return response.choices[0].message["content"].strip()

        except Exception as e:
            error_msg = f"Error with model '{model}': {e}"
            error_messages.append(error_msg)

    # If both attempts fail, return a combined error message
    return (
        "All attempts to generate a response failed. Detailed errors:\n\n"
        + "\n".join(error_messages)
    )

# ------------------------------------------------------------------------------
# 4) Streamlit UI
# ------------------------------------------------------------------------------
st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")

# Text area for job description / input
input_text = st.text_area("Job Description:", key="input")

# File uploader for PDF resume
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])
if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")

# Buttons
submit1 = st.button("Tell Me About the Resume")
submit3 = st.button("Percentage Match (Full ATS Analysis)")

# ------------------------------------------------------------------------------
# SYSTEM PROMPTS (AGENTS) FOR DIFFERENT USE CASES
# ------------------------------------------------------------------------------
base_system_prompt = (
    "You are an advanced ATS (Applicant Tracking System) and HR assistant. "
    "You will receive two pieces of text: 1) a job description (JD), 2) an extracted resume. "
    "Use your specialized capabilities to provide thorough, professional analysis. "
    "If the resume text is truncated, do your best with what is provided."
)

# Prompt for a simpler, high-level resume evaluation
input_prompt1 = """
You are an experienced Technical HR Manager. 
Review the provided resume text against the job description.
Share your professional evaluation: 
- Does the candidate’s profile match the role?
- Highlight overall strengths and weaknesses relevant to the specified job requirements.
- Focus on clarity and a general overview, rather than detailed numeric scoring.
"""

# Prompt for a complete ATS analysis, including:
#   1) JD Keywords & Weighting
#   2) Tech Stack vs. Projects Cross-Check
#   3) Experience Analysis
#   4) Certification Verification
#   5) Score Normalization & Final Report
input_prompt3 = """
You are a specialized ATS (Applicant Tracking System) with the following tasks:

1) **JD Keywords & Weighting**:
   - Automatically extract the top skills/keywords from the job description.
   - Assign higher priority if the JD suggests they are critical.

2) **Tech Stack vs. Projects Cross-Check**:
   - Identify the candidate’s claimed technical skills.
   - Examine Projects to confirm whether each claimed skill was actually used.
   - Flag any skills claimed but not demonstrated.

3) **Experience Analysis**:
   - Verify time consistency (overlapping dates, etc.).
   - Identify gaps in employment.
   - Evaluate role durations vs. job requirements.

4) **Certification Verification**:
   - Identify certifications.
   - Evaluate their relevance, validity, and domain mapping.

5) **Score Normalization & Final Report**:
   - Combine all analysis into a final “percentage match” or “ATS score.”
   - Provide missing keywords.
   - Summarize the analysis with sub-scores for keywords, skill-project match, experience, and certifications.
   - Give final recommendations.

Address these points thoroughly in your response.
"""

# ------------------------------------------------------------------------------
# Button logic for "Tell Me About the Resume"
# ------------------------------------------------------------------------------
if submit1:
    if uploaded_file is not None:
        try:
            # 1) Extract text from PDF
            pdf_text = extract_text_from_pdf(uploaded_file)

            # 2) Combine job description + resume text in a user message
            user_message = f"""
            Job Description:
            {input_text}

            Resume Text:
            {pdf_text}
            """

            # 3) Get OpenAI response (High-level evaluation)
            response = get_openai_response(
                system_prompt=base_system_prompt,
                user_message=user_message + "\n" + input_prompt1
            )

            st.subheader("The Response is:")
            st.write(response)

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload a resume before clicking this button.")

# ------------------------------------------------------------------------------
# Button logic for "Percentage Match (Full ATS Analysis)"
# ------------------------------------------------------------------------------
elif submit3:
    if uploaded_file is not None:
        try:
            # 1) Extract text from PDF
            pdf_text = extract_text_from_pdf(uploaded_file)

            # 2) Combine job description + resume text in a user message
            user_message = f"""
            Job Description:
            {input_text}

            Resume Text:
            {pdf_text}
            """

            # 3) Get OpenAI response (Complete ATS analysis)
            response = get_openai_response(
                system_prompt=base_system_prompt,
                user_message=user_message + "\n" + input_prompt3
            )

            st.subheader("The Response is:")
            st.write(response)

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload a resume before clicking this button.")
