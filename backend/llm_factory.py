"""
FinanX — LLM Factory
Konfigürasyona göre doğru LLM nesnesini döndürür (Google Gemini veya OpenAI).
"""

from loguru import logger
from backend.config import settings


def get_llm():
    """
    Ayarlara göre LangChain LLM nesnesi döndür.
    LLM_PROVIDER = "google" → Gemini 1.5 Pro
    LLM_PROVIDER = "openai" → GPT-4o
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info(f"LLM: Google Gemini ({settings.LLM_MODEL})")
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            max_output_tokens=4096,
            convert_system_message_to_human=True,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        logger.info(f"LLM: OpenAI ({settings.LLM_MODEL})")
        return ChatOpenAI(
            model=settings.LLM_MODEL or "gpt-4o",
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
            max_tokens=4096,
        )
    else:
        raise ValueError(
            f"Geçersiz LLM_PROVIDER: '{provider}'. "
            "Desteklenenler: 'google', 'openai'"
        )


def get_fast_llm():
    """
    Hızlı işlemler için (router, sınıflandırma) daha küçük/hızlı model.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,
            max_output_tokens=512,
            convert_system_message_to_human=True,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.0,
            max_tokens=512,
        )
    else:
        return get_llm()
