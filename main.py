import os
import sys
import hashlib
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.agent import generar_cv_adaptado
from src.compiler import compile_pdf
from src.llm_provider import obtener_proveedor

def calcular_hash_archivos(*rutas: Path, extra: str = "") -> str:
    """Calcula un hash conjunto para detectar si los archivos de entrada o la configuración cambiaron."""
    hasher = hashlib.sha256()
    for ruta in rutas:
        if ruta.exists():
            hasher.update(ruta.read_bytes())
    if extra:
        hasher.update(extra.encode("utf-8"))
    return hasher.hexdigest()

def validar_archivos_entrada(ruta_cv: Path, ruta_oferta: Path):
    """Evita quemar tokens con archivos vacíos o inexistentes."""
    for ruta, nombre in [(ruta_cv, "CV base"), (ruta_oferta, "Oferta laboral")]:
        if not ruta.exists():
            raise FileNotFoundError(f"Falta el archivo: {ruta}. Colócalo en 'input/'.")
        
        # Validar tamaño mínimo (evita llamar al LLM con archivos vacíos)
        contenido = ruta.read_text(encoding="utf-8").strip()
        if len(contenido) < 50:
            raise ValueError(f"El archivo '{nombre}' ({ruta}) parece estar vacío o es demasiado corto.")

def main():
    parser = argparse.ArgumentParser(description="Adaptador de CV en LaTeX optimizado.")
    parser.add_argument("--force", action="store_true", help="Fuerza la llamada a la IA ignorando la caché.")
    parser.add_argument("--provider", "--proveedor", dest="provider", type=str, default=None,
                        help="Proveedor LLM: gemini, openai, claude (defecto: gemini o variable LLM_PROVIDER)")
    parser.add_argument("--model", "--modelo", dest="model", type=str, default=None,
                        help="Modelo específico del proveedor (ej: gpt-4o, claude-sonnet-4-20250514)")
    parser.add_argument("--mode", "--modo", dest="mode", type=str,
                        choices=["main_cv_based", "full_tailored"],
                        default=os.environ.get("TAILORING_MODE", "main_cv_based"),
                        help="Modo de adaptación: 'main_cv_based' (fiel al CV, recomendado) o 'full_tailored' (adaptación total).")
    args = parser.parse_args()

    print("=" * 55)
    print("         Agente Adaptador de CV en LaTeX          ")
    print("=" * 55)

    dir_entrada = Path("input")
    dir_salida = Path("output")
    dir_entrada.mkdir(exist_ok=True)
    dir_salida.mkdir(exist_ok=True)

    ruta_cv_base = dir_entrada / "base_cv.tex"
    ruta_oferta = dir_entrada / "job_description.txt"
    ruta_salida_tex = dir_salida / "tailored_cv.tex"
    ruta_hash = dir_salida / ".last_run.hash"

    try:
        # 1. Validación previa (0 costo de tokens si falla)
        validar_archivos_entrada(ruta_cv_base, ruta_oferta)

        # 2. Control de Caché: Verificar si las entradas o la configuración cambiaron
        config_extra = f"{args.provider}_{args.model}_{args.mode}"
        hash_actual = calcular_hash_archivos(ruta_cv_base, ruta_oferta, extra=config_extra)
        hash_previo = ruta_hash.read_text().strip() if ruta_hash.exists() else None

        debe_regenerar = args.force or (hash_actual != hash_previo) or not ruta_salida_tex.exists()

        if debe_regenerar:
            print(f"🔄 Cambios detectados o flag --force activo. Llamando a la API (Modo: {args.mode})...")
            
            # Instanciar proveedor LLM
            proveedor = obtener_proveedor(
                nombre_proveedor=args.provider,
                modelo=args.model,
            )

            # Paso 1: Ejecutar agente optimizado (debe retornar tex y metadata)
            resultado = generar_cv_adaptado(
                ruta_cv_base=str(ruta_cv_base),
                ruta_oferta=str(ruta_oferta),
                ruta_salida_tex=str(ruta_salida_tex),
                proveedor=proveedor,
                modo=args.mode,
            )

            # Guardamos el hash solo tras una generación exitosa
            ruta_hash.write_text(hash_actual)
        else:
            print("⚡ Las entradas y configuración no han cambiado. Usando 'tailored_cv.tex' en caché (0 tokens consumidos).")
            print("💡 (Usa 'python main.py --force' si deseas regenerarlo de todos modos).")

        # Paso 2: Compilar el PDF
        print("⚙️  Compilando PDF...")
        compile_pdf(
            tex_path=str(ruta_salida_tex),
            output_dir=str(dir_salida)
        )

        print("-" * 55)
        print("🎉 ¡Proceso completado con éxito!")
        print(f"📄 Archivo listo en: {dir_salida / 'tailored_cv.pdf'}")
        print("-" * 55)

    except (FileNotFoundError, ValueError) as e:
        print(f"\n❌ Error de validación: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()