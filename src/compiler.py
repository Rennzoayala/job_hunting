import subprocess
import shutil
import sys
from pathlib import Path

def compile_pdf(tex_path: str, output_dir: str) -> Path:
    """Compiles a .tex file into a PDF in the designated output directory."""
    tex_file = Path(tex_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("📄 Compiling LaTeX file to PDF...")

    # Compiler selection: 'tectonic' handles downloads automatically; fallback to 'pdflatex'
    if shutil.which("tectonic"):
        cmd = ["tectonic", "-o", str(out_dir), str(tex_file)]
    elif shutil.which("pdflatex"):
        cmd = ["pdflatex", f"-output-directory={out_dir}", str(tex_file)]
    else:
        raise RuntimeError(
            "\n❌ No LaTeX compiler detected.\n"
            "Run 'pip install tectonic' or install a LaTeX distribution (MiKTeX, TeX Live, MacTeX)."
        )

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        pdf_path = out_dir / f"{tex_file.stem}.pdf"
        print(f"✅ PDF compiled successfully at: {pdf_path}")
        return pdf_path
    except subprocess.CalledProcessError as e:
        print("\n❌ Error during LaTeX compilation:")
        print(e.stderr or e.stdout)
        sys.exit(1)