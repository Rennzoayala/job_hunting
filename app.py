import os
import sys
from pathlib import Path
import streamlit as st

# Ensure UTF-8 output encoding for console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Attempt loading .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.agent import generar_cv_adaptado
from src.compiler import compile_pdf

# Page configuration
st.set_page_config(
    page_title="Job Hunting - CV Tailor",
    page_icon="📄",
    layout="wide"
)

# App Header
st.title("📄 Job Hunting: AI CV Tailor")
st.markdown(
    "Tailor your LaTeX CV to any job description in seconds using Google Gemini. "
    "Get recruiter-optimized bullet points, matched skills, and ready-to-use output."
)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key Input
    saved_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API Key:",
        value=saved_key,
        type="password",
        help="Get a free key from Google AI Studio: https://aistudio.google.com/app/apikey"
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input.strip()

    st.markdown("[🔑 Get a free Gemini API Key](https://aistudio.google.com/app/apikey)")

    st.markdown("---")
    st.subheader("Model Selection")
    model_choice = st.selectbox(
        "Gemini Model:",
        options=["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview"],
        index=0,
        help="Recommended: gemini-3.8-flash or gemini-3.5-flash-lite"
    )
    os.environ["LLM_MODEL"] = model_choice

    st.markdown("---")
    st.subheader("Output Format")
    output_mode = st.radio(
        "Choose what to generate:",
        options=[
            "📄 Render PDF & LaTeX (Requires Tectonic)",
            "📝 LaTeX Code Only (Fast, Overleaf-ready)"
        ],
        index=0,
        help="Select whether to compile into a PDF or just generate the adapted LaTeX code."
    )

    st.markdown("---")
    st.caption("💡 **Tip:** If you use Overleaf or an external LaTeX editor, choose 'LaTeX Code Only' to quickly copy the result.")

# Ensure input & output directories exist
dir_input = Path("input")
dir_output = Path("output")
dir_input.mkdir(exist_ok=True)
dir_output.mkdir(exist_ok=True)

# Main Form Layout
col1, col2 = st.columns(2)

# Column 1: Base CV
with col1:
    st.subheader("1. Base CV (LaTeX)")
    cv_input_method = st.radio(
        "CV Input Method:",
        options=["Upload .tex file", "Paste LaTeX code", "Use input/base_cv.tex"],
        horizontal=True
    )
    
    cv_content = ""
    if cv_input_method == "Upload .tex file":
        uploaded_cv = st.file_uploader("Upload your base CV (.tex)", type=["tex", "txt"])
        if uploaded_cv:
            cv_content = uploaded_cv.getvalue().decode("utf-8", errors="replace")
    elif cv_input_method == "Paste LaTeX code":
        cv_content = st.text_area(
            "Paste your complete LaTeX CV code here:",
            height=300,
            placeholder=r"\documentclass{article}..."
        )
    else:
        existing_cv_path = dir_input / "base_cv.tex"
        if existing_cv_path.exists():
            cv_content = existing_cv_path.read_text(encoding="utf-8", errors="replace")
            st.info(f"Loaded existing file: `input/base_cv.tex` ({len(cv_content)} chars)")
        else:
            st.warning("File `input/base_cv.tex` not found. Please upload or paste your CV.")

# Column 2: Job Description
with col2:
    st.subheader("2. Job Description")
    job_input_method = st.radio(
        "Job Description Input Method:",
        options=["Paste text", "Upload text file", "Use input/job_description.txt"],
        horizontal=True
    )
    
    job_content = ""
    if job_input_method == "Paste text":
        job_content = st.text_area(
            "Paste the job description / posting here:",
            height=300,
            placeholder="We are looking for a Senior Software Engineer with experience in..."
        )
    elif job_input_method == "Upload text file":
        uploaded_job = st.file_uploader("Upload job description file (.txt)", type=["txt", "md"])
        if uploaded_job:
            job_content = uploaded_job.getvalue().decode("utf-8", errors="replace")
    else:
        existing_job_path = dir_input / "job_description.txt"
        if existing_job_path.exists():
            job_content = existing_job_path.read_text(encoding="utf-8", errors="replace")
            st.info(f"Loaded existing file: `input/job_description.txt` ({len(job_content)} chars)")
        else:
            st.warning("File `input/job_description.txt` not found. Please paste or upload the job posting.")

st.markdown("---")

# Generate Button
generate_btn = st.button("🚀 Generate Tailored CV", type="primary", use_container_width=True)

if generate_btn:
    # 1. Validations
    if not os.environ.get("GEMINI_API_KEY"):
        st.error("❌ Please provide a valid **Gemini API Key** in the sidebar settings.")
        st.stop()
        
    if not cv_content or len(cv_content.strip()) < 50:
        st.error("❌ The Base CV is empty or too short (must be at least 50 characters).")
        st.stop()

    if not job_content or len(job_content.strip()) < 50:
        st.error("❌ The Job Description is empty or too short (must be at least 50 characters).")
        st.stop()

    # Save inputs to disk for processing
    path_cv_base = dir_input / "base_cv.tex"
    path_oferta = dir_input / "job_description.txt"
    path_salida_tex = dir_output / "tailored_cv.tex"

    path_cv_base.write_text(cv_content, encoding="utf-8")
    path_oferta.write_text(job_content, encoding="utf-8")

    # 2. Execution
    try:
        with st.spinner("🤖 Analyzing CV and job description with Gemini AI..."):
            tex_final, analisis_estrategico = generar_cv_adaptado(
                ruta_cv_base=str(path_cv_base),
                ruta_oferta=str(path_oferta),
                ruta_salida_tex=str(path_salida_tex),
                modelo_por_defecto=model_choice,
                retornar_analisis=True
            )

        pdf_path = None
        if "Render PDF" in output_mode:
            with st.spinner("⚙️ Compiling PDF with Tectonic..."):
                pdf_path = compile_pdf(
                    tex_path=str(path_salida_tex),
                    output_dir=str(dir_output)
                )

        st.success("🎉 CV successfully generated and tailored!")

        # Action Buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if pdf_path and pdf_path.exists():
                pdf_bytes = pdf_path.read_bytes()
                st.download_button(
                    label="⬇️ Download Tailored PDF",
                    data=pdf_bytes,
                    file_name="tailored_cv.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.info("ℹ️ PDF rendering was skipped (LaTeX Code Only mode).")

        with btn_col2:
            st.download_button(
                label="⬇️ Download LaTeX Code (.tex)",
                data=tex_final.encode("utf-8"),
                file_name="tailored_cv.tex",
                mime="text/plain",
                use_container_width=True
            )

        # Strategic Plan & Code Preview
        st.markdown("### 📋 Results & Insights")
        
        tab_plan, tab_code = st.tabs(["🎯 Strategic Recruiter Action Plan", "📝 LaTeX Code Preview"])
        
        with tab_plan:
            st.markdown(analisis_estrategico)

        with tab_code:
            st.code(tex_final, language="latex")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
