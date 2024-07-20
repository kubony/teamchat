import utils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from loguru import logger
from config.settings import settings

st.set_page_config(page_title="컨텍스트 인식 챗봇", page_icon="⭐")
st.header('컨텍스트 인식 챗봇')
st.write('컨텍스트 인식을 통한 챗봇 상호작용 향상')

class ContextChatbot:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
    
    @st.cache_resource
    def setup_chain(_self, max_tokens=1000):
        memory = ConversationBufferMemory(max_token_limit=max_tokens)
        chain = ConversationChain(llm=_self.llm, memory=memory, verbose=True)
        return chain
    
    @utils.enable_chat_history
    def main(self):
        max_tokens = st.sidebar.slider("메모리 크기 (토큰)", 100, 2000, 1000)
        chain = self.setup_chain(max_tokens)
        user_query = st.chat_input(placeholder="무엇이든 물어보세요!")
        if user_query:
            utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamHandler(st.empty())
                try:
                    result = chain.invoke(
                        {"input": user_query},
                        {"callbacks": [st_cb]}
                    )
                    response = result["response"]
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    logger.info(f"사용자 질문: {user_query}")
                    logger.info(f"챗봇 응답: {response}")
                except Exception as e:
                    error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    st.sidebar.title("설정")
    model = st.sidebar.selectbox("LLM 모델 선택", [settings.DEFAULT_MODEL, "다른모델1", "다른모델2"])
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
    
    obj = ContextChatbot()
    obj.main()