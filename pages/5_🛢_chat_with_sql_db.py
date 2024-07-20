import utils
import sqlite3
import streamlit as st
from pathlib import Path
from sqlalchemy import create_engine
from loguru import logger
from config.settings import settings

from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities.sql_database import SQLDatabase

st.set_page_config(page_title="SQL 챗봇", page_icon="🛢")
st.header('SQL 데이터베이스와 대화하기')
st.write('간단한 대화형 명령을 통해 SQL 데이터베이스와 상호작용할 수 있는 챗봇입니다.')

class SqlChatbot:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
    
    def setup_db(self, db_uri):
        try:
            if db_uri == 'USE_SAMPLE_DB':
                db_filepath = (Path(__file__).parent.parent / "assets/Chinook.db").absolute()
                db_uri = f"sqlite:////{db_filepath}"
                creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
                db = SQLDatabase(create_engine("sqlite:///", creator=creator))
            else:
                db = SQLDatabase.from_uri(database_uri=db_uri)
            
            with st.sidebar.expander('데이터베이스 테이블', expanded=True):
                st.info('\n- '+'\n- '.join(db.get_usable_table_names()))
            return db
        except Exception as e:
            logger.error(f"데이터베이스 설정 중 오류 발생: {str(e)}")
            st.error(f"데이터베이스 연결 중 오류가 발생했습니다: {str(e)}")
            st.stop()
    
    def setup_sql_agent(self, db):
        try:
            agent = create_sql_agent(
                llm=self.llm,
                db=db,
                top_k=10,
                verbose=True,
                agent_type="openai-tools",
                handle_parsing_errors=True,
                handle_sql_errors=True
            )
            return agent
        except Exception as e:
            logger.error(f"SQL 에이전트 설정 중 오류 발생: {str(e)}")
            st.error(f"SQL 에이전트 설정 중 오류가 발생했습니다: {str(e)}")
            st.stop()

    @utils.enable_chat_history
    def main(self):
        # 사용자 입력
        radio_opt = ['샘플 DB 사용 - Chinook.db', '사용자 SQL DB 연결']
        selected_opt = st.sidebar.radio(
            label='옵션 선택',
            options=radio_opt
        )
        if radio_opt.index(selected_opt) == 1:
            with st.sidebar.popover(':orange[⚠️ 보안 주의사항]', use_container_width=True):
                warning = "SQL 데이터베이스의 Q&A 시스템을 구축하려면 모델이 생성한 SQL 쿼리를 실행해야 합니다. 이 과정에는 고유한 위험이 있습니다. 데이터베이스 연결 권한이 체인/에이전트의 필요에 맞게 항상 최소한으로 제한되어 있는지 확인하세요.\n\n일반적인 보안 모범 사례에 대한 자세한 내용은 [여기](https://python.langchain.com/docs/security)를 참조하세요."
                st.warning(warning)
            db_uri = st.sidebar.text_input(
                label='데이터베이스 URI',
                placeholder='mysql://user:pass@hostname:port/db'
            )
        else:
            db_uri = 'USE_SAMPLE_DB'
        
        if not db_uri:
            st.error("계속하려면 데이터베이스 URI를 입력하세요!")
            st.stop()
        
        db = self.setup_db(db_uri)
        agent = self.setup_sql_agent(db)

        user_query = st.chat_input(placeholder="무엇이든 물어보세요!")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container())
                try:
                    result = agent.invoke(
                        {"input": user_query},
                        {"callbacks": [st_cb]}
                    )
                    response = result["output"]
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.write(response)
                    logger.info(f"사용자 질문: {user_query}")
                    logger.info(f"챗봇 응답: {response}")
                except Exception as e:
                    error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                    st.error(error_msg)
                    logger.error(error_msg)

if __name__ == "__main__":
    obj = SqlChatbot()
    obj.main()