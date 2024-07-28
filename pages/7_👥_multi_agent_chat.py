# pages/7_👥_multi_agent_chat.py
import os
import json
import utils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatAnthropic
from loguru import logger
from config.settings import settings
import random

st.set_page_config(page_title="다중 AI 에이전트 채팅", page_icon="💬")
st.header('다중 AI 에이전트 채팅')
st.write('여러 AI 에이전트가 참여하는 단체 채팅방입니다.')

class MultiAgentChat:
    def __init__(self):
        utils.sync_st_session()
        self.agents = {}
        self.shared_memory = ConversationBufferMemory(input_key="human_input", memory_key="history", max_token_limit=4000)
        self.agents = self.setup_agents()
        self.moderator = self.setup_moderator()
        self.baton = 0
        self.conversation_history = []
        self.log_file = 'agent_interactions.jsonl'

    def setup_agents(self):
        agents = {}
        for agent_name, agent_info in settings.AGENTS.items():
            if agent_name != "moderator":
                agents[agent_name] = {
                    'context': self.load_role_context(agent_name, agent_info['role']),
                    'chain': self.setup_chain(agent_info['model'], agent_name)
                }
        return agents
    
    def load_role_context(self, role, role_description):
        context = f"당신의 역할은 {role}입니다. {role_description}\n\n"
        path = os.path.join(os.getcwd(), 'role_contexts', f"{role}.md")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as file:
                context += file.read()
        return context

    def setup_chain(self, model, agent_name):
        if model.startswith('claude-'):
            llm = ChatAnthropic(model=model, anthropic_api_key=settings.ANTHROPIC_API_KEY.get_secret_value())
        else:
            llm = utils.configure_llm_with_model(model)
        
        prompt = PromptTemplate(
            input_variables=["context", "history", "human_input"],
            template="""역할 컨텍스트:
    {context}

    대화 내용:
    {history}

    당신은 {human_input} 역할입니다. 위의 대화 내용을 모두 고려하여 다음 발언을 해주세요. 다른 에이전트들의 의견도 고려하세요:"""
        )
        
        return LLMChain(llm=llm, prompt=prompt, memory=self.shared_memory, verbose=False)

    def setup_moderator(self):
        moderator_info = settings.AGENTS["moderator"]
        llm = utils.configure_llm_with_model(moderator_info['model'])
        prompt = PromptTemplate(
            input_variables=["history", "agents", "human_input"],
            template="대화 내용: {history}\n\n다음 발언자를 {agents} 중에서 선택하고, 대화를 계속할 바톤 수(1-5)를 결정해주세요. 형식: '발언자:바톤수'\n\n사용자 입력: {human_input}"
        )
        return LLMChain(llm=llm, prompt=prompt, memory=self.shared_memory, verbose=False)
  
    def get_next_speaker(self):
        agent_names = [name for name in settings.AGENTS.keys() if name != "moderator"]
        response = self.moderator.predict(
            history=self.get_conversation_history_string(),
            agents=', '.join(agent_names),
            human_input="다음 발언자를 선택하고, 대화를 계속할 바톤 수(1-5)를 결정해주세요. 형식: '발언자:바톤수'"
        )
        response = response.strip().lower()
        
        # 응답 파싱 로직 개선
        parts = response.split(':')
        if len(parts) >= 2:
            next_speaker = parts[0].strip()
            try:
                self.baton = max(1, min(5, int(parts[1].strip())))
            except ValueError:
                self.baton = 1
                logger.warning(f"Invalid baton count: {parts[1]}. Setting to 1.")
        else:
            next_speaker = response
            self.baton = 1
            logger.warning(f"Invalid response format: {response}. Using default values.")
        
        if next_speaker not in agent_names or next_speaker == self.conversation_history[-1].split(':')[0]:
            logger.warning(f"Invalid speaker selected: {next_speaker}. Selecting randomly from others.")
            available_speakers = [name for name in agent_names if name != self.conversation_history[-1].split(':')[0]]
            next_speaker = random.choice(available_speakers)
        
        logger.info(f"Next speaker: {next_speaker}, Baton count: {self.baton}")
        return next_speaker

    def log_interaction(self, role, prompt, response):
        log_entry = {
            "role": role,
            "prompt": prompt,
            "response": str(response)
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')

    def add_to_conversation_history(self, message):
        self.conversation_history.append(message)
        self.shared_memory.save_context({"human_input": message}, {"output": ""})

    def get_conversation_history_string(self):
        return "\n".join(self.conversation_history[-10:])

    @utils.enable_chat_history
    def main(self):
        user_query = st.chat_input(placeholder="대화를 시작하세요!")
        
        if user_query:
            self.add_to_conversation_history(f"User: {user_query}")
            utils.display_msg(user_query, 'user')
            self.baton = 1
            logger.info(f"대화 시작: 바톤 카운트 {self.baton}", extra={"action": "start_conversation"})
            
            while self.baton > 0:
                next_speaker = self.get_next_speaker()
                
                with st.chat_message("assistant"):
                    st_cb = StreamHandler(st.empty())
                    try:
                        agent = self.agents[next_speaker]
                        conversation_history = self.get_conversation_history_string()
                        
                        response = agent['chain'].predict(
                            context=agent['context'],
                            history=conversation_history,
                            human_input=next_speaker,
                            callbacks=[st_cb]
                        )

                        st.markdown(f"**{next_speaker}**: {response}")
                        
                        self.add_to_conversation_history(f"{next_speaker}: {response}")
                        logger.info(f"{next_speaker} 응답: {utils.truncate_string(response)}", extra={"action": "agent_response", "agent": next_speaker})
                        
                        self.log_interaction(next_speaker, utils.truncate_string(conversation_history), utils.truncate_string(response))
                        
                        self.baton -= 1
                        logger.info(f"바톤 카운트 감소: {self.baton}", extra={"action": "decrease_baton"})
                    
                    except Exception as e:
                        error_msg = f"응답 생성 중 오류 발생: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"상세 오류 정보: {type(e).__name__}, {str(e)}", extra={"action": "error"})
                        logger.exception("스택 트레이스:")
                        break
            
            logger.info(f"대화 종료: 바톤 카운트 {self.baton}", extra={"action": "end_conversation"})

if __name__ == "__main__":
    obj = MultiAgentChat()
    obj.main()