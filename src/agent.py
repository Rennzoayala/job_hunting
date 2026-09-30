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
    modelo_por_defecto: str = "gemini-3.6-flash",
    retornar_analisis: bool = False
):
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
        "Eres un Reclutador Técnico y Auditor de CVs experto. Tu idioma base y obligatorio es el ESPAÑOL. "
        "Sé conciso y directo. No des bienvenidas ni explicaciones largas; genera únicamente viñetas de acción. "
        "IMPORTANTE: No uses asteriscos dobles (**) para resaltar nombres de tecnologías o herramientas "
        "(ej. escribe 'Node.js, React, Python y MongoDB' de forma natural y limpia, NUNCA '**Node.js**, **React**')."
    )

    prompt_analisis = f"""
IDIOMA OBLIGATORIO: Todo el análisis debe estar redactado en ESPAÑOL.

OFERTA DE TRABAJO:
{descripcion_puesto}

CUERPO ACTUAL DEL CV:
{cuerpo_cv}

Genera un plan de acción conciso en ESPAÑOL (máx. 400 palabras):
1. Palabras clave y tecnologías obligatorias a incluir (sin negritas ni asteriscos en cada palabra).
2. Viñetas específicas a transformar usando verbos de acción en español y métricas (formato: Acción + Contexto + Resultado).
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
        "Eres un compilador y redactor experto en LaTeX. Tu idioma base de redacción es estrictamente el ESPAÑOL. "
        "Devuelve ÚNICAMENTE el contenido modificado que va entre \\begin{document} y \\end{document}. "
        "REGLAS CRÍTICAS DE FORMATO:\n"
        "1. PROHIBIDO usar formato Markdown dentro del código LaTeX (NUNCA uses asteriscos dobles como **texto** ni simples *texto*).\n"
        "2. No resaltes con asteriscos listas de habilidades o tecnologías (escribe 'Node.js, React, Python y MongoDB', jamás '**Node.js**, **React**...').\n"
        "3. Si un comando original de LaTeX usa \\textbf{...}, mantén la sintaxis nativa de LaTeX, pero nunca agregues sintaxis Markdown.\n"
        "4. No incluyas bloques markdown (sin ```latex), no agregues preámbulo ni comentarios explicativos.\n"
        "5. Toda la redacción de viñetas, logros y descripciones del CV debe ser en ESPAÑOL."
    )

    prompt_redactor = f"""
IDIOMA OBLIGATORIO: ESPAÑOL. Adapta y redacta todas las descripciones en ESPAÑOL.

PLAN DE MODIFICACIONES:
{analisis_estrategico}

CUERPO ORIGINAL EN LATEX (a modificar):
{cuerpo_cv}

REGLAS ESTRICTAS:
- Redacta todas las nuevas viñetas, experiencias y habilidades en ESPAÑOL.
- Mantén la estructura de secciones, comandos y formato original de LaTeX intactos.
- CERO MARKDOWN: Jamás coloques asteriscos **palabra** en el LaTeX. Escribe texto limpio.
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

    # Si el LLM incluyó \begin{document} o preámbulo duplicado, extraer únicamente el contenido interior
    if r"\begin{document}" in nuevo_cuerpo:
        nuevo_cuerpo = re.split(r"\\begin\{document\}", nuevo_cuerpo, maxsplit=1)[1]

    if r"\end{document}" in nuevo_cuerpo:
        nuevo_cuerpo = re.split(r"\\end\{document\}", nuevo_cuerpo, maxsplit=1)[0]

    nuevo_cuerpo = nuevo_cuerpo.strip()

    # Salvaguarda: Eliminar cualquier asterisco markdown residual en el código LaTeX (**texto** -> texto)
    nuevo_cuerpo = re.sub(r"\*\*(.+?)\*\*", r"\1", nuevo_cuerpo)

    # Reconstrucción determinística del documento LaTeX en Python
    if preambulo and cierre:
        tex_final = f"{preambulo.rstrip()}\n{nuevo_cuerpo}\n{cierre.lstrip()}"
    else:
        tex_final = nuevo_cuerpo

    with open(ruta_salida_tex, "w", encoding="utf-8") as f:
        f.write(tex_final)

    print(f"✅ CV adaptado y guardado en: {ruta_salida_tex}")
    if retornar_analisis:
        return tex_final, analisis_estrategico
    return tex_final