# Non‑Technical User Guide for *Job Hunting* CV Tailor

A quick, beginner-friendly guide to tailoring your resume/CV for any job posting using Google Gemini AI and LaTeX—no coding required!

---

## 1. How to Launch the Application

You do not need to use terminal commands or write any code.

1. Open the project folder (`Job_hunting`).
2. **Double‑click the file named `run_app.bat`**.
3. A small window will appear and your default web browser (Chrome, Edge, Firefox, etc.) will automatically open to the **CV Tailor** interface:
   ```
   http://localhost:8501
   ```

*(When you are done, simply close your browser tab and close the command window).*

---

## 2. Quick Setup (Sidebar)

On the left side of your browser screen, you will see the **Settings** sidebar:

1. **Gemini API Key**:
   - If you have an API key, paste it into the **Gemini API Key** box.
   - If you already set it in your `.env` file, it will be filled in automatically.
   - *Don't have a key?* It's free! Click the link in the sidebar or visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate one.
2. **Output Format**:
   - **📄 Render PDF & LaTeX (Default)**: Generates the adapted LaTeX and compiles it into a ready-to-send PDF file.
   - **📝 LaTeX Code Only**: Generates only the adapted LaTeX code. Use this if you want instant results without PDF compilation, or if you prefer copying the code directly into [Overleaf](https://www.overleaf.com).

---

## 3. How to Use the App

### Step 1: Provide Your Base CV
In the **Base CV** section (left column):
- **Upload .tex file**: Click Browse to select your existing LaTeX CV (`.tex` or `.txt`).
- **Paste LaTeX code**: Or directly paste your full LaTeX code into the box.
- **Use input/base_cv.tex**: Automatically loads the CV file stored in the `input/` folder.

### Step 2: Provide the Job Description
In the **Job Description** section (right column):
- **Paste text**: Simply copy the job posting from LinkedIn, Indeed, or the company career page and paste it into the box.
- **Upload text file**: Or upload a `.txt` file containing the job posting.

### Step 3: Generate
Click the big blue button: **🚀 Generate Tailored CV**.

---

## 4. Getting Your Results

Once the AI finishes analyzing and rewriting your CV:

1. **Download Buttons**:
   - **⬇️ Download Tailored PDF**: Downloads the compiled PDF (`tailored_cv.pdf`) directly to your Downloads folder.
   - **⬇️ Download LaTeX Code (.tex)**: Downloads the source LaTeX document.
2. **Results & Insights Tabs**:
   - **🎯 Strategic Recruiter Action Plan**: Read what the AI recruiter changed, which keywords were injected, and which accomplishments were highlighted.
   - **📝 LaTeX Code Preview**: View and copy the generated LaTeX code directly to your clipboard.

---

## 5. Troubleshooting & FAQ

| Problem | Cause & Solution |
|---------|------------------|
| *“Please provide a valid Gemini API Key”* | You need to enter your Google Gemini API key in the left sidebar. Get a free one at [Google AI Studio](https://aistudio.google.com/app/apikey). |
| *“CV / Job Description is too short”* | Make sure both inputs contain actual content (at least 50 characters). |
| *“Error during LaTeX compilation”* | If you are using Windows and PDF compilation fails, make sure the free [Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) is installed. Alternatively, select **LaTeX Code Only** in the sidebar to bypass PDF compilation and open the code in Overleaf! |
| *“How do I save my API key so I don't re-enter it?”* | Create or edit a file named `.env` in the project folder and add: `GEMINI_API_KEY=your_actual_key_here`. The app will load it automatically every time. |

---

## 6. Alternative: Running from Command Line (For Tech Users)

If you prefer using the terminal, you can still launch the app or run the batch script:
```powershell
streamlit run app.py
```
or run the CLI tool directly:
```powershell
python main.py --force
```
