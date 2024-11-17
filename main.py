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
안녕하세요!
저는 편한 주문 서비스 Holtz입니다.
주문하고 싶은 매장을 왼쪽 메뉴에서 선택해주세요!

- **더치앤빈 서울창업허브점** : 운영 중인 매장입니다.
- **서울창업허브 3층** : 준비 중인 매장입니다.
- **앤틀러 파운더스페이스** : 준비 중인 매장입니다.
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