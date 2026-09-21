import os
import re
from google import genai
from google.genai import types

def separar_latex(contenido_tex: str):
    """Separa el preámbulo del cuerpo del documento para ahorrar tokens."""
    patron = r"(\\begin\{document\})(.*?)(\\end\{document\})"
    match = re.search(patron, contenido_tex, flags=re.DOTALL)
    if match:
        preambulo = contenido_tex[:match.start(2)]
        cuerpo = match.group(2)
        cierre = contenido_tex[match.end(2):]
        return preambulo, cuerpo, cierre
    return "", contenido_tex, ""

def generar_cv_adaptado(
    ruta_cv_base: str, 
    ruta_oferta: str, 
    ruta_salida_tex: str,
    modelo_por_defecto: str = "gemini-3.6-flash"
) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Falta GEMINI_API_KEY.")

    llm_model = os.environ.get("LLM_MODEL") or modelo_por_defecto

    if not os.path.exists(ruta_cv_base) or not os.path.exists(ruta_oferta):
        raise FileNotFoundError("Verifica las rutas del CV base y la oferta.")

    client = genai.Client(api_key=api_key)

    with open(ruta_cv_base, "r", encoding="utf-8") as f:
        cv_completo = f.read()

    with open(ruta_oferta, "r", encoding="utf-8") as f:
        descripcion_puesto = f.read()

    # 1. Separamos preámbulo: Evitamos que el LLM lo procese y lo genere de vuelta
    preambulo, cuerpo_cv, cierre = separar_latex(cv_completo)

    # -------------------------------------------------------------------------
    # PASO 1: Estratega & Reclutador (Fusión de Agentes 1 y 2)
    # -------------------------------------------------------------------------
    print(f"🎯 [Paso 1/2] Analizando CV contra oferta (Modelo: {llm_model})...")

    sys_instruction_1 = (
        "Eres un Reclutador Técnico y Auditor de CVs. Sé conciso y directo. "
        "No des bienvenidas ni explicaciones largas; genera únicamente viñetas de acción."
    )

    prompt_analisis = f"""
OFERTA DE TRABAJO:
{descripcion_puesto}

CUERPO ACTUAL DEL CV:
{cuerpo_cv}

Genera un plan de acción conciso (máx. 400 palabras):
1. Palabras clave / tecnologías obligatorias a incluir.
2. Viñetas específicas a transformar usando verbos de acción y métricas (formato: Acción + Contexto + Resultado).
3. Elementos a omitir o sintetizar por falta de relevancia con la oferta.
"""

    analisis_estrategico = client.models.generate_content(
        model=llm_model,
        contents=prompt_analisis,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction_1,
            temperature=0.2,
            max_output_tokens=700  # Evita respuestas intermedias verbosas
        )
    ).text

    # -------------------------------------------------------------------------
    # PASO 2: Redactor de LaTeX (Solo reescribe el cuerpo interior)
    # -------------------------------------------------------------------------
    print("✍️  [Paso 2/2] Reescribiendo el cuerpo del CV en LaTeX...")

    sys_instruction_2 = (
        "Eres un compilador y redactor experto en LaTeX. Devuelve ÚNICAMENTE el contenido "
        "modificado que va entre \\begin{document} y \\end{document}. "
        "No incluyas markdown (sin ```latex), no agregues preámbulo ni comentarios."
    )

    prompt_redactor = f"""
PLAN DE MODIFICACIONES:
{analisis_estrategico}

CUERPO ORIGINAL EN LATEX (a modificar):
{cuerpo_cv}

REGLAS:
- Mantén la estructura de secciones, comandos y formato original intactos.
- Solo actualiza redacción, viñetas y habilidades según el plan.
"""

    response = client.models.generate_content(
        model=llm_model,
        contents=prompt_redactor,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction_2,
            temperature=0.2
        )
    )

    nuevo_cuerpo = response.text.strip()
    nuevo_cuerpo = re.sub(r"^```(?:latex)?\n?", "", nuevo_cuerpo, flags=re.IGNORECASE)
    nuevo_cuerpo = re.sub(r"\n?```$", "", nuevo_cuerpo).strip()

    # Reconstrucción determinística del documento LaTeX en Python
    tex_final = f"{preambulo}{nuevo_cuerpo}{cierre}" if preambulo else nuevo_cuerpo

    with open(ruta_salida_tex, "w", encoding="utf-8") as f:
        f.write(tex_final)

    print(f"✅ CV adaptado y guardado en: {ruta_salida_tex}")
    return tex_final