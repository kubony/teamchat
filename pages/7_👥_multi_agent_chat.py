# pages/7_👥_multi_agent_chat.py
import os
import json
import utils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from loguru import logger
from config.settings import settings
import random

st.set_page_config(page_title="다중 AI 에이전트 채팅", page_icon="💬")
st.header('다중 AI 에이전트 채팅')
st.write('여러 AI 에이전트가 참여하는 단체 채팅방입니다.')

class MultiAgentChat:
    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.roles = self.load_roles()
        self.agents = self.setup_agents()
        self.moderator = self.setup_moderator()
        self.baton = 0
        self.conversation_history = []
        self.log_file = 'agent_interactions.jsonl'
    
    def load_roles(self):
        with open('roles.json', 'r') as f:
            return json.load(f)
        
    def setup_agents(self):
        agents = {}
        for role in self.roles:
            agents[role] = {
                'context': self.load_role_context(role),
                'chain': self.setup_chain()
            }
        return agents
    
    def load_role_context(self, role):
        context = f"당신의 역할은 {role}입니다. {self.roles[role]}\n\n"
        path = os.path.join(os.getcwd(), 'role_contexts', f"{role}.md")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as file:
                context += file.read()
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
        moderator_input = f"대화 내용: {' '.join(self.conversation_history)}\n\n다음 발언자를 {', '.join(self.roles.keys())} 중에서 선택하세요. 선택한 역할의 이름만 답변으로 제시하세요."
        response = self.moderator.invoke({"input": moderator_input})
        next_speaker = response['response'].strip().lower()
        
        if next_speaker not in self.roles:
            logger.warning(f"Invalid speaker selected: {next_speaker}. Defaulting to {list(self.roles.keys())[0]}.")
            return list(self.roles.keys())[0]
        
        return next_speaker
    
    def log_interaction(self, role, prompt, response):
        log_entry = {
            "role": role,
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
                        full_query = f"역할 컨텍스트:\n{agent['context']}\n\n대화 내용: {' '.join(self.conversation_history)}\n\n당신은 {next_speaker} 역할입니다. 다음 발언:"
                        result = agent['chain'].invoke(
                            {"input": full_query},
                            {"callbacks": [st_cb]}
                        )
                        response = result["response"]
                        self.conversation_history.append(f"{next_speaker}: {response}")
                        st.session_state.messages.append({"role": "assistant", "content": f"{next_speaker}: {response}"})
                        logger.info(f"{next_speaker} 응답: {response}")
                        
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