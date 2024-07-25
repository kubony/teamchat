# pages/7_👥_multi_agent_chat.py
import os
import json
import utils
import streamlit as st
from streaming import StreamHandler
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger
from config.settings import settings
import random
from anthropic import Anthropic

st.set_page_config(page_title="다중 AI 에이전트 채팅", page_icon="💬")
st.header('다중 AI 에이전트 채팅')
st.write('여러 AI 에이전트가 참여하는 단체 채팅방입니다.')

class MultiAgentChat:
    def __init__(self):
        utils.sync_st_session()
        self.agents = {}  # 여기서 self.agents를 초기화합니다.
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
                    'memory': ConversationBufferMemory(max_token_limit=2000),
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
            return Anthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())
        else:
            llm = utils.configure_llm_with_model(model)
            memory = ConversationBufferMemory(max_token_limit=2000)
            chain = ConversationChain(llm=llm, memory=memory, verbose=False)
            return chain

    def setup_moderator(self):
        moderator_info = settings.AGENTS["moderator"]
        llm = utils.configure_llm_with_model(moderator_info['model'])
        memory = ConversationBufferMemory(max_token_limit=2000)
        return ConversationChain(llm=llm, memory=memory, verbose=False)
    
    def get_next_speaker(self):
        agent_names = [name for name in settings.AGENTS.keys() if name != "moderator"]
        moderator_input = f"대화 내용: {self.get_conversation_history_string()}\n\n다음 발언자를 {', '.join(agent_names)} 중에서 선택하세요. 선택한 역할의 이름만 답변으로 제시하세요."
        response = self.moderator.invoke({"input": moderator_input})
        next_speaker = response['response'].strip().lower()
        
        if next_speaker not in agent_names or next_speaker == self.conversation_history[-1].split(':')[0]:
            logger.warning(f"Invalid speaker selected: {next_speaker}. Selecting randomly from others.")
            available_speakers = [name for name in agent_names if name != self.conversation_history[-1].split(':')[0]]
            return random.choice(available_speakers)
        
        return next_speaker
    
    def log_interaction(self, role, prompt, response):
        log_entry = {
            "role": role,
            "prompt": prompt,
            "response": str(response)  # 문자열로 변환
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')

    def add_to_conversation_history(self, message):
        self.conversation_history.append(message)
        # 모든 에이전트의 메모리에 메시지 추가
        for agent in self.agents.values():
            agent['memory'].chat_memory.add_user_message(message)

    def get_conversation_history_string(self):
        return "\n".join(self.conversation_history[-10:])  # 최근 10개의 메시지만 포함

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
                        full_query = f"""역할 컨텍스트:\n{agent['context']}\n\n
대화 내용:\n{conversation_history}\n\n
당신은 {next_speaker} 역할입니다. 위의 대화 내용을 모두 고려하여 다음 발언을 해주세요. 다른 에이전트들의 의견도 고려하세요:"""
                        
                        if isinstance(agent['chain'], Anthropic):
                            # Claude 모델 사용
                            logger.debug("Using Anthropic API for agent: %s", next_speaker)
                            message = agent['chain'].messages.create(
                                model="claude-3-5-sonnet-20240620",
                                max_tokens=1000,
                                temperature=0,
                                system=agent['context'],
                                messages=[
                                    {"role": "user", "content": conversation_history},
                                    {"role": "user", "content": full_query}
                                ]
                            )
                            response = message.content[0].text if isinstance(message.content, list) else message.content
                            st_cb.on_llm_new_token(response)
                        else:
                            # 다른 모델 사용
                            logger.debug("Using other model for agent: %s", next_speaker)
                            result = agent['chain'].invoke(
                                {"input": full_query},
                                {"callbacks": [st_cb]}
                            )
                            response = result["response"]

                        response_str = str(response)
                        
                        st.markdown(f"**{next_speaker}**: {response_str}")
                        
                        self.add_to_conversation_history(f"{next_speaker}: {response_str}")
                        logger.info(f"{next_speaker} 응답: {utils.truncate_string(response_str)}", extra={"action": "agent_response", "agent": next_speaker})
                        
                        self.log_interaction(next_speaker, utils.truncate_string(full_query), utils.truncate_string(response_str))
                        
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