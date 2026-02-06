from langchain_openai import ChatOpenAI

from app.mode.config.config import ALI_LLM_BASE_URL, ALI_LLM_KEY


def create_ali_llm(model_name: str):
    # 通过 langchain_openai 引入大模型,创建模型实体

    chat_llm = ChatOpenAI(
        model=model_name,
        base_url = ALI_LLM_BASE_URL,
        api_key = ALI_LLM_KEY,
    )
    return chat_llm