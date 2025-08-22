import logging
import os
import threading
from datetime import datetime, timedelta
from typing import Dict

from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

conversation_states: Dict[str, Dict] = {}
memory_lock = threading.Lock()
MEMORY_EXPIRATION_MINUTES = 30


def get_or_create_memory(chat_id: str) -> ConversationBufferWindowMemory:
    with memory_lock:
        if chat_id not in conversation_states:
            log.info(f"Criando nova memória para o chatId: {chat_id}")
            memory = ConversationBufferWindowMemory(
                k=15, memory_key="chat_history", return_messages=True
            )
            conversation_states[chat_id] = {
                "memory": memory,
                "last_activity": datetime.now()
            }
        else:
            log.info(f"Reutilizando memória existente para o chatId: {chat_id}")
            conversation_states[chat_id]["last_activity"] = datetime.now()

        return conversation_states[chat_id]["memory"]


def clean_old_memories():
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
            log.info(f"Memória para o chatId: {chat_id} expirada e removida.")

    log.info("Limpeza de memórias antigas concluída.")


def start_memory_cleaner():
    clean_old_memories()
    threading.Timer(300, start_memory_cleaner).start()


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente virtual amigável e prestativo. Responda de forma educada e concisa."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

conversation_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True,
)


async def run_agent(chat_id: str, message: str) -> str:
    log.info(f"Executando para chatId: {chat_id} com mensagem: '{message}'")

    if not message.strip():
        log.warning(f"Mensagem vazia recebida para chatId: {chat_id}")
        return "Por favor, envie uma mensagem válida."

    memory = get_or_create_memory(chat_id)

    try:
        response = await conversation_chain.apredict(
            input=message,
            chat_history=memory.chat_memory.messages
        )

        memory.save_context({"input": message}, {"output": response})

        log.info(f"Resposta do agente para chatId {chat_id}: '{response}'")
        return response

    except Exception as e:
        log.error(f"Erro ao executar o agente para chatId {chat_id}: {e}", exc_info=True)
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."


start_memory_cleaner()