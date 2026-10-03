"""
Capa de abstracción de proveedores LLM.
Soporta: Gemini, OpenAI, Claude (Anthropic).
"""

import os
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Registro & Fábrica
# ---------------------------------------------------------------------------

REGISTRO_PROVEEDORES: dict[str, type["ProveedorLLM"]] = {}

MODELOS_POR_DEFECTO = {
    "gemini": "gemini-3.6-flash",
    "openai": "gpt-4o-mini",
    "claude": "claude-sonnet-4-20250514",
}

VARS_API_KEY = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


def obtener_proveedor(
    nombre_proveedor: str | None = None,
    modelo: str | None = None,
    api_key: str | None = None,
) -> "ProveedorLLM":
    """Fábrica: construye el proveedor correcto según nombre + overrides opcionales."""
    nombre = (nombre_proveedor or os.environ.get("LLM_PROVIDER", "gemini")).lower().strip()

    if nombre not in REGISTRO_PROVEEDORES:
        disponibles = ", ".join(sorted(REGISTRO_PROVEEDORES))
        raise ValueError(
            f"Proveedor '{nombre}' no soportado. Disponibles: {disponibles}"
        )

    clave = api_key or os.environ.get(VARS_API_KEY.get(nombre, ""))
    if not clave:
        raise ValueError(
            f"Falta la API key para el proveedor '{nombre}'. "
            f"Configura la variable de entorno {VARS_API_KEY.get(nombre, '???')}."
        )

    modelo_resuelto = modelo or os.environ.get("LLM_MODEL") or MODELOS_POR_DEFECTO.get(nombre, "")
    cls = REGISTRO_PROVEEDORES[nombre]
    return cls(api_key=clave, modelo=modelo_resuelto)


# ---------------------------------------------------------------------------
# Clase Base Abstracta
# ---------------------------------------------------------------------------

class ProveedorLLM(ABC):
    """Interfaz que todo backend LLM debe implementar."""

    def __init_subclass__(cls, nombre_proveedor: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if nombre_proveedor:
            REGISTRO_PROVEEDORES[nombre_proveedor] = cls

    def __init__(self, api_key: str, modelo: str):
        self.api_key = api_key
        self.modelo = modelo

    @property
    @abstractmethod
    def nombre(self) -> str: ...

    @abstractmethod
    def generar(
        self,
        prompt: str,
        instruccion_sistema: str = "",
        temperatura: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Envía un prompt de un solo turno y retorna la respuesta como texto."""
        ...


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class ProveedorGemini(ProveedorLLM, nombre_proveedor="gemini"):
    @property
    def nombre(self) -> str:
        return "gemini"

    def generar(self, prompt, instruccion_sistema="", temperatura=0.2, max_tokens=None):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "El paquete 'google-genai' no está instalado. "
                "Ejecuta: pip install google-genai"
            )

        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            system_instruction=instruccion_sistema or None,
            temperature=temperatura,
        )
        if max_tokens:
            config.max_output_tokens = max_tokens

        response = client.models.generate_content(
            model=self.modelo,
            contents=prompt,
            config=config,
        )
        return response.text


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class ProveedorOpenAI(ProveedorLLM, nombre_proveedor="openai"):
    @property
    def nombre(self) -> str:
        return "openai"

    def generar(self, prompt, instruccion_sistema="", temperatura=0.2, max_tokens=None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "El paquete 'openai' no está instalado. "
                "Ejecuta: pip install openai"
            )

        client = OpenAI(api_key=self.api_key)
        mensajes = []
        if instruccion_sistema:
            mensajes.append({"role": "system", "content": instruccion_sistema})
        mensajes.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.modelo,
            "messages": mensajes,
            "temperature": temperatura,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------

class ProveedorClaude(ProveedorLLM, nombre_proveedor="claude"):
    @property
    def nombre(self) -> str:
        return "claude"

    def generar(self, prompt, instruccion_sistema="", temperatura=0.2, max_tokens=None):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "El paquete 'anthropic' no está instalado. "
                "Ejecuta: pip install anthropic"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperatura,
            "max_tokens": max_tokens or 4096,  # Anthropic requiere max_tokens
        }
        if instruccion_sistema:
            kwargs["system"] = instruccion_sistema

        response = client.messages.create(**kwargs)
        return response.content[0].text
