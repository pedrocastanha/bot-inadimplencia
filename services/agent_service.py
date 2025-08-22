import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Dict

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool  # Para criar tools custom

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

MEMORY_EXPIRATION_MINUTES = 30
conversation_states: Dict[str, Dict] = {}
memory_lock = threading.Lock()

@tool
async def consultar_divida(cliente_id: str) -> str:
    """
    Consulta o status de dívida de um cliente pelo ID.
    Simulação; em produção, chame uma API ou banco de dados.
    """
    return f"Cliente {cliente_id} tem dívida de R$ 500,00 vencida em 15/08/2024."

tools = [consultar_divida]

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
    async_client=True  # Habilita chamadas assíncronas
)

system_message = """
Você é um assistente de atendimento ao cliente para uma empresa de cobrança de inadimplentes.
Seja educado, empático e ofereça opções de pagamento. Nunca ameace ou use linguagem agressiva.
Pergunte por detalhes necessários (ex.: ID do cliente) se não fornecidos.
Use ferramentas disponíveis para consultar informações.
Exemplos:
- Usuário: "Tenho uma dívida"
  Resposta: "Entendo, posso ajudar! Por favor, informe seu ID de cliente para que eu possa verificar os detalhes da sua dívida."
- Usuário: "Quero parcelar"
  Resposta: "Ótimo! Por favor, forneça seu ID de cliente para que eu possa consultar o valor e oferecer opções de parcelamento."
- Após consultar dívida: "Sua dívida é de R$ X, vencida em Y. Podemos parcelar em até Z vezes com desconto de W% se pago até [data]. Deseja prosseguir?"
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    handle_parsing_errors=True
)

def get_or_create_memory(chat_id: str) -> ConversationBufferWindowMemory:
    """
    Retorna a memória de conversa para um dado chat_id, ou cria uma nova se não existir.
    Atualiza o timestamp da última atividade.
    """
    with memory_lock:
        if chat_id not in conversation_states:
            log.info(f"Criando nova memória para o chat_id: {chat_id}")
            conversation_states[chat_id] = {
                'memory': ConversationBufferWindowMemory(k=20, memory_key="chat_history", return_messages=True),
                'last_activity': datetime.now()
            }
        else:
            log.info(f"Reutilizando memória existente para o chat_id: {chat_id}")
            conversation_states[chat_id]['last_activity'] = datetime.now()
        return conversation_states[chat_id]['memory']

def clean_old_memories():
    """
    Limpa memórias de conversa que expiraram.
    Esta função deve ser executada periodicamente.
    """
    log.info("Iniciando limpeza de memórias antigas...")
    current_time = datetime.now()
    expired_threshold = timedelta(minutes=MEMORY_EXPIRATION_MINUTES)
    with memory_lock:
        chat_ids_to_remove = [
            chat_id for chat_id, state in conversation_states.items()
            if (current_time - state['last_activity']) > expired_threshold
        ]
        for chat_id in chat_ids_to_remove:
            del conversation_states[chat_id]
            log.info(f"Memória para o chat_id: {chat_id} expirada e removida.")
    log.info("Limpeza de memórias antigas concluída.")

# Inicia um thread para limpeza periódica (a cada 5 minutos)
def start_memory_cleaner():
    clean_old_memories()
    threading.Timer(300, start_memory_cleaner).start()

start_memory_cleaner()

async def run_agent(chat_id: str, message: str) -> str:
    """
    Executa o agente LangChain para uma dada mensagem e chat_id.
    Gerencia a memória da conversa.
    """
    log.info(f"Executando agente para chat_id: {chat_id} com mensagem: '{message}'")

    if not message.strip():
        log.warning(f"Mensagem vazia recebida para chat_id: {chat_id}")
        return "Por favor, envie uma mensagem válida."

    memory = get_or_create_memory(chat_id)
    try:
        result = await agent_executor.ainvoke({
            "input": message,
        "chat_history": memory.load_memory_variables({})["chat_history"
        ]})
        response = result.get("output", "Desculpe, não consegui processar sua solicitação.")
        log.info(f"Resposta do agente para chat_id {chat_id}: '{response}'")
        return response
    except Exception as e:
        log.error(f"Erro ao executar o agente para chat_id {chat_id}: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."