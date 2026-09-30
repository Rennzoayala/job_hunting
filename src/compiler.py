import subprocess
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def detectar_compilador() -> str:
    """Busca tectonic en la raíz del proyecto o en el PATH del sistema."""
    # 1. Buscar tectonic.exe en la raíz del proyecto
    ruta_raiz = Path(__file__).resolve().parent.parent
    local_tectonic = ruta_raiz / "tectonic.exe"
    if local_tectonic.exists():
        return str(local_tectonic)

    # 2. Buscar en PATH del sistema
    tectonic_en_path = shutil.which("tectonic") or shutil.which("tectonic.exe")
    if tectonic_en_path:
        return tectonic_en_path

    # 3. Fallback a pdflatex si existiera
    pdflatex_en_path = shutil.which("pdflatex")
    if pdflatex_en_path:
        return pdflatex_en_path

    return None

def compile_pdf(tex_path: str, output_dir: str) -> Path:
    """Compila un archivo .tex a PDF en el directorio especificado."""
    tex_file = Path(tex_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    compilador = detectar_compilador()
    if not compilador:
        raise RuntimeError(
            "\n❌ No se detectó compilador LaTeX.\n"
            "Asegúrate de que 'tectonic.exe' esté en la carpeta raíz del proyecto."
        )

    print(f"📄 Compiling LaTeX file to PDF using: {Path(compilador).name}...")

    # Construcción del comando según el compilador detectado
    if "tectonic" in compilador.lower():
        # --print fuerza a Tectonic a mostrar el log de errores si falla
        cmd = [compilador, "--print", "-o", str(out_dir), str(tex_file)]
    else:
        cmd = [compilador, f"-output-directory={out_dir}", str(tex_file)]

    try:
        # Forzamos encoding='utf-8' para no perder caracteres en Windows
        subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding="utf-8", 
            errors="replace"
        )
        pdf_path = out_dir / f"{tex_file.stem}.pdf"
        print(f"✅ PDF compiled successfully at: {pdf_path}")
        return pdf_path

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 55)
        print(f"❌ Error during LaTeX compilation (Código de salida: {e.returncode}):")
        print("=" * 55)
        
        salida_completa = ""
        if e.stdout and e.stdout.strip():
            salida_completa += f"\n[OUTPUT]:\n{e.stdout.strip()}"
        if e.stderr and e.stderr.strip():
            salida_completa += f"\n[STDERR]:\n{e.stderr.strip()}"
            
        if salida_completa:
            print(salida_completa)
        else:
            print("El ejecutable no emitió texto.")
            # Diagnóstico según el código de retorno típico de Windows:
            if e.returncode in (-1073741515, 3221225781):
                print("💡 Causa probable: Falta 'Visual C++ Redistributable' en Windows (vcruntime140.dll).")
            elif e.returncode in (-1073741819, 3221225477):
                print("💡 Causa probable: Conflicto de permisos o antivirus bloqueando el binario.")
            else:
                print("💡 Ejecuta en tu terminal: .\\tectonic.exe .\\output\\tailored_cv.tex -o .\\output")
                print("   para ver la respuesta directa de la consola.")
        print("=" * 55)
        raise RuntimeError(f"Error during LaTeX compilation (exit code {e.returncode}):\n{salida_completa}")