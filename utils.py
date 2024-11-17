# utils.py
import os
import openai
import streamlit as st
from datetime import datetime
from loguru import logger
from config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
import anthropic
from anthropic import Anthropic

def setup_logging():
    logger.add("logs/app.log", rotation="500 MB", level="INFO")
    if settings.OPENAI_API_KEY:
        logger.info(f"OPENAI_API_KEY loaded: {settings.OPENAI_API_KEY.get_secret_value()[:5]}...{settings.OPENAI_API_KEY.get_secret_value()[-5:]}")
    else:
        logger.error("OPENAI_API_KEY is not set in the environment variables.")

setup_logging()

def enable_chat_history(func):
    if settings.OPENAI_API_KEY:
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except KeyError:
                pass

        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "주문하시겠어요? 메뉴를 골라주세요!"}]
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])

    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute

def display_msg(msg, author):
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def get_openai_model_list(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        gpt_models = [{"id": m.id, "created": datetime.fromtimestamp(m.created)} for m in models if m.id.startswith("gpt")]
        return sorted(gpt_models, key=lambda x: x["created"], reverse=True)
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI 인증 오류: {str(e)}")
        st.error("OpenAI API 키가 유효하지 않습니다.")
        st.stop()
    except Exception as e:
        logger.error(f"OpenAI 모델 목록 조회 중 오류 발생: {str(e)}")
        st.error("모델 목록을 가져오는 중 오류가 발생했습니다. 나중에 다시 시도해주세요.")
        st.stop()

def configure_llm():
    available_llms = [settings.DEFAULT_MODEL, "llama3:8b", "OpenAI API 키 사용"]
    llm_opt = st.sidebar.radio("LLM 선택", options=available_llms, key="SELECTED_LLM")

    if llm_opt == "llama3:8b":
        return ChatOllama(model="llama3", base_url=settings.OLLAMA_ENDPOINT)
    elif llm_opt == settings.DEFAULT_MODEL:
        return ChatOpenAI(model_name=llm_opt, temperature=0, streaming=True, api_key=settings.OPENAI_API_KEY.get_secret_value())
    else:
        openai_api_key = st.sidebar.text_input("OpenAI API 키", type="password", placeholder="sk-...", key="CUSTOM_OPENAI_API_KEY")
        if not openai_api_key:
            st.error("계속하려면 OpenAI API 키를 입력해주세요.")
            st.info("API 키는 다음 링크에서 얻을 수 있습니다: https://platform.openai.com/account/api-keys")
            st.stop()

        available_models = get_openai_model_list(openai_api_key)
        model = st.sidebar.selectbox("모델 선택", options=[m["id"] for m in available_models], key="SELECTED_OPENAI_MODEL")
        return ChatOpenAI(model_name=model, temperature=0, streaming=True, api_key=openai_api_key)

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v

def configure_llm_with_model(model_name):
    if model_name.startswith('claude-'):
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())
        return client
    elif model_name.startswith('gpt-'):
        return ChatOpenAI(model_name=model_name, temperature=0, streaming=True, api_key=settings.OPENAI_API_KEY.get_secret_value())
    else:
        return ChatOllama(model=model_name, base_url=settings.OLLAMA_ENDPOINT)
    
def truncate_string(s, max_length=100):
    return s if len(s) <= max_length else s[:max_length] + '...'

def setup_logging():
    logger.add("logs/app.log", rotation="500 MB", level="INFO")
    logger.add(lambda msg: print(truncate_string(msg)), level="INFO")
    if settings.OPENAI_API_KEY:
        logger.info(f"OPENAI_API_KEY loaded: {settings.OPENAI_API_KEY.get_secret_value()[:5]}...{settings.OPENAI_API_KEY.get_secret_value()[-5:]}")
    else:
        logger.error("OPENAI_API_KEY is not set in the environment variables.")