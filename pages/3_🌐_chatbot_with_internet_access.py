import utils
import streamlit as st
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from loguru import logger
from config.settings import settings

st.set_page_config(page_title="인터넷 챗봇", page_icon="🌐")
st.header('인터넷 접근이 가능한 챗봇')
st.write('인터넷 접근 기능을 갖추어 최신 이벤트에 대한 질문에 답변할 수 있습니다.')

class InternetChatbot:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()

    @st.cache_resource(show_spinner='연결 중..')
    def setup_agent(_self):
        # 도구 정의
        ddg_search = DuckDuckGoSearchRun()
        tools = [
            Tool(
                name="DuckDuckGoSearch",
                func=ddg_search.run,
                description="현재 사건에 대한 질문에 답할 때 유용합니다. 구체적인 질문을 해야 합니다.",
            )
        ]

        # 프롬프트 가져오기
        prompt = hub.pull("hwchase17/react-chat")

        # LLM 및 에이전트 설정
        memory = ConversationBufferMemory(memory_key="chat_history")
        agent = create_react_agent(_self.llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)
        return agent_executor, memory

    @utils.enable_chat_history
    def main(self):
        agent_executor, memory = self.setup_agent()
        user_query = st.chat_input(placeholder="무엇이든 물어보세요!")
        if user_query:
            utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container())
                try:
                    result = agent_executor.invoke(
                        {"input": user_query, "chat_history": memory.chat_memory.messages},
                        {"callbacks": [st_cb]}
                    )
                    response = result["output"]
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.write(response)
                    
                    # 검색 결과 출처 표시 (있는 경우)
                    if "source" in result:
                        st.info(f"정보 출처: {result['source']}")
                    
                    logger.info(f"사용자 질문: {user_query}")
                    logger.info(f"챗봇 응답: {response}")
                except Exception as e:
                    error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    st.sidebar.title("설정")
    search_engine = st.sidebar.selectbox("검색 엔진", ["DuckDuckGo", "Google", "Bing"])
    max_search_results = st.sidebar.slider("최대 검색 결과 수", 1, 10, 3)
    
    obj = InternetChatbot()
    obj.main()