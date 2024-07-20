import streamlit as st
from loguru import logger

st.set_page_config(
    page_title="Langchain 챗봇",
    page_icon='💬',
    layout='wide'
)

logger.info("메인 페이지 로드됨")

st.header("Langchain을 활용한 챗봇 구현")

st.write("""
Langchain은 언어 모델(LLMs)을 사용하는 애플리케이션 개발을 간소화하기 위해 설계된 강력한 프레임워크입니다. 
다양한 구성 요소를 포괄적으로 통합하여 강력한 애플리케이션을 만드는 과정을 단순화합니다.

Langchain의 능력을 활용하면 챗봇 생성이 쉬워집니다. 다음은 다양한 사용 사례에 맞춘 챗봇 구현의 예시들입니다:

- **기본 챗봇**: LLM과 대화형 상호작용을 할 수 있습니다.
- **컨텍스트 인식 챗봇**: 이전 대화를 기억하고 그에 따라 응답을 제공하는 챗봇입니다.
- **인터넷 접근 가능 챗봇**: 최근 사건에 대한 사용자 질문에 답변할 수 있는 인터넷 지원 챗봇입니다.
- **문서 기반 챗봇**: 사용자 정의 문서에 접근할 수 있는 능력을 갖춘 챗봇으로, 참조된 정보를 바탕으로 사용자 질문에 답변할 수 있습니다.
- **SQL 데이터베이스 챗봇**: 간단한 대화형 명령을 통해 SQL 데이터베이스와 상호작용할 수 있는 챗봇입니다.

각 챗봇의 사용 예시를 탐색하려면 해당 챗봇 섹션으로 이동하세요.
""")

# 버전 정보 표시
st.sidebar.text("버전: 1.0.0")

# 피드백 섹션
st.sidebar.text_input("피드백", placeholder="여기에 피드백을 입력하세요")
if st.sidebar.button("피드백 제출"):
    # 피드백 처리 로직을 여기에 추가할 수 있습니다.
    logger.info("사용자가 피드백을 제출함")
    st.sidebar.success("피드백을 주셔서 감사합니다!")

logger.info("메인 페이지 렌더링 완료")