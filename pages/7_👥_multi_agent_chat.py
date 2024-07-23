import os
import utils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from loguru import logger
from config.settings import settings
import random
import json

st.set_page_config(page_title="다중 AI 에이전트 채팅", page_icon="💬")
st.header('다중 AI 에이전트 채팅')
st.write('여러 AI 에이전트가 참여하는 단체 채팅방입니다.')

class MultiAgentChat:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.agents = self.setup_agents()
        self.moderator = self.setup_moderator()
        self.baton = 0
        self.conversation_history = []
        self.log_file = 'agent_interactions.jsonl'
        
    def setup_agents(self):
        agents = {}
        agent_folders = ['agent1', 'agent2', 'agent3']
        for folder in agent_folders:
            agents[folder] = {
                'context': self.load_agent_context(folder),
                'chain': self.setup_chain()
            }
        return agents
    
    def load_agent_context(self, folder):
        context = ""
        path = os.path.join(os.getcwd(), folder)
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.endswith('.md'):
                    with open(os.path.join(path, filename), 'r', encoding='utf-8') as file:
                        context += f"\n\n{filename}:\n{file.read()}"
        return context
    
    def setup_chain(self):
        memory = ConversationBufferMemory(max_token_limit=1000)
        chain = ConversationChain(llm=self.llm, memory=memory, verbose=True)
        return chain
    
    def setup_moderator(self):
        moderator_context = "당신은 대화를 분석하고 다음 발언자를 선택하는 사회자입니다."
        memory = ConversationBufferMemory(max_token_limit=1000)
        return ConversationChain(llm=self.llm, memory=memory, verbose=True)
    
    def get_next_speaker(self):
        moderator_input = f"대화 내용: {' '.join(self.conversation_history)}\n\n다음 발언자를 'agent1', 'agent2', 또는 'agent3' 중에서 선택하세요. 선택한 에이전트의 이름만 답변으로 제시하세요."
        response = self.moderator.invoke({"input": moderator_input})
        next_speaker = response['response'].strip().lower()
        
        if next_speaker not in ['agent1', 'agent2', 'agent3']:
            logger.warning(f"Invalid speaker selected: {next_speaker}. Defaulting to agent1.")
            return 'agent1'
        
        return next_speaker
    
    def log_interaction(self, agent, prompt, response):
        log_entry = {
            "agent": agent,
            "prompt": prompt,
            "response": response
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
    
    @utils.enable_chat_history
    def main(self):
        user_query = st.chat_input(placeholder="대화를 시작하세요!")
        
        if user_query:
            self.conversation_history.append(f"User: {user_query}")
            utils.display_msg(user_query, 'user')
            self.baton = 3
            logger.info(f"대화 시작: 바톤 카운트 {self.baton}")
            
            while self.baton > 0:
                next_speaker = self.get_next_speaker()
                
                with st.chat_message("assistant"):
                    st_cb = StreamHandler(st.empty())
                    try:
                        agent = self.agents[next_speaker]
                        full_query = f"에이전트 컨텍스트:\n{agent['context']}\n\n대화 내용: {' '.join(self.conversation_history)}\n\n당신은 {next_speaker}입니다. 다음 발언:"
                        result = agent['chain'].invoke(
                            {"input": full_query},
                            {"callbacks": [st_cb]}
                        )
                        response = result["response"]
                        self.conversation_history.append(f"{next_speaker}: {response}")
                        st.session_state.messages.append({"role": "assistant", "content": f"{next_speaker}: {response}"})
                        logger.info(f"{next_speaker} 응답: {response}")
                        
                        # 프롬프트와 응답 로깅
                        self.log_interaction(next_speaker, full_query, response)
                        
                        self.baton -= 1
                        logger.info(f"바톤 카운트 감소: {self.baton}")
                    
                    except Exception as e:
                        error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"상세 오류 정보: {type(e).__name__}, {str(e)}")
                        logger.exception("스택 트레이스:")
                        break
            
            logger.info(f"대화 종료: 바톤 카운트 {self.baton}")

if __name__ == "__main__":
    obj = MultiAgentChat()
    obj.main()