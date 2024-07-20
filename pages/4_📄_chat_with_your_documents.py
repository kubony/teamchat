import os
import utils
import streamlit as st
from streaming import StreamHandler
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from config.settings import settings

st.set_page_config(page_title="문서 챗봇", page_icon="📄")
st.header('문서 기반 챗봇 (기본 RAG)')
st.write('사용자 정의 문서에 접근하여 문서 내용을 참조해 사용자 질문에 답변할 수 있습니다.')

class CustomDataChatbot:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()

    def save_file(self, file):
        folder = 'tmp'
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        file_path = f'./{folder}/{file.name}'
        with open(file_path, 'wb') as f:
            f.write(file.getvalue())
        return file_path

    @st.spinner('문서 분석 중..')
    def setup_qa_chain(self, uploaded_files):
        try:
            # 문서 로드
            docs = []
            for file in uploaded_files:
                file_path = self.save_file(file)
                loader = PyPDFLoader(file_path)
                docs.extend(loader.load())
                os.remove(file_path)  # 임시 파일 삭제
            
            # 문서 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)

            # 임베딩 생성 및 벡터 DB 저장
            embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
            vectordb = DocArrayInMemorySearch.from_documents(splits, embeddings)

            # 검색기 정의
            retriever = vectordb.as_retriever(
                search_type='mmr',
                search_kwargs={'k': self.k, 'fetch_k': self.fetch_k}
            )

            # 컨텍스트 대화를 위한 메모리 설정        
            memory = ConversationBufferMemory(
                memory_key='chat_history',
                output_key='answer',
                return_messages=True
            )

            # LLM 및 QA 체인 설정
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=True,
                verbose=True
            )
            return qa_chain
        except Exception as e:
            logger.error(f"QA 체인 설정 중 오류 발생: {str(e)}")
            raise

    @utils.enable_chat_history
    def main(self):
        # 사용자 입력
        uploaded_files = st.sidebar.file_uploader(label='PDF 파일 업로드', type=['pdf'], accept_multiple_files=True)
        if not uploaded_files:
            st.error("계속하려면 PDF 문서를 업로드해주세요!")
            st.stop()

        # 사용자 설정
        self.k = st.sidebar.slider("검색할 문서 수", 1, 5, 2)
        self.fetch_k = st.sidebar.slider("후보 문서 수", 1, 10, 4)

        user_query = st.chat_input(placeholder="무엇이든 물어보세요!")

        if uploaded_files and user_query:
            try:
                qa_chain = self.setup_qa_chain(uploaded_files)
                utils.display_msg(user_query, 'user')

                with st.chat_message("assistant"):
                    st_cb = StreamHandler(st.empty())
                    result = qa_chain.invoke(
                        {"question": user_query},
                        {"callbacks": [st_cb]}
                    )
                    response = result["answer"]
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # 참조 표시
                    for idx, doc in enumerate(result['source_documents'], 1):
                        filename = os.path.basename(doc.metadata['source'])
                        page_num = doc.metadata['page']
                        ref_title = f":blue[참조 {idx}: *{filename} - 페이지 {page_num}*]"
                        with st.popover(ref_title):
                            st.caption(doc.page_content)

                logger.info(f"사용자 질문: {user_query}")
                logger.info(f"챗봇 응답: {response}")
            except Exception as e:
                error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                st.error(error_msg)
                logger.error(error_msg)

if __name__ == "__main__":
    obj = CustomDataChatbot()
    obj.main()