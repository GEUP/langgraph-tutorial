import operator
from typing import Annotated, List, TypedDict, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from dotenv import load_dotenv
import json

load_dotenv()

# 1. FastAPI 앱 설정
app = FastAPI(title="LangGraph Agent API")

# 2. LLM 및 그래프 설정 (기존 로직 유지)
# 실제 배포시에는 base_url이 컨테이너 내부 네트워크나 외부 API를 가리켜야 합니다.
llm = ChatOpenAI(
    temperature=0.0,
    base_url="http://host.docker.internal:1234/v1", # Docker에서 로컬 호스트 접근시 (Mac/Win)
    api_key="not-needed",
    model="openai/gpt-oss-20b"
)

class ChatLogState(TypedDict):
    logs: Annotated[List[BaseMessage], operator.add]

# 3. 노드 로직 수정: input() 제거 -> 외부 입력을 받을 준비
def chat_node(state: ChatLogState) -> Command:
    # API 구조에서는 interrupt("wait user message")를 직접 쓰기보다
    # 클라이언트가 보낸 메시지를 받아서 바로 처리하는 구조가 더 적합할 수 있습니다.
    # 하지만 Human-in-the-loop를 유지하려면 checkpointer가 필수입니다.

    # 여기서는 간단히 마지막 메시지를 받아서 응답하는 구조로 시연합니다.
    last_message = state['logs'][-1]

    # LLM 호출
    response = llm.invoke(state['logs'])

    return Command(
        update={"logs": [response]},
        # goto는 상황에 따라 설정. API는 한 턴하고 끝나는 경우가 많음
        goto=END
    )

memory = MemorySaver()
builder = StateGraph(ChatLogState)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")

# checkpointer 필수 (상태 유지를 위해)
graph = builder.compile(checkpointer=memory)

# 4. 요청 모델 정의
class ChatRequest(BaseModel):
    thread_id: str
    message: str

# 5. API 엔드포인트 생성
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    사용자 메시지를 받아서 LangGraph를 실행하고 결과를 스트리밍으로 반환
    """
    thread_id = request.thread_id
    user_input = request.message

    config = {"configurable": {"thread_id": thread_id}}

    # 사용자 메시지를 상태에 주입 (HumanMessage)
    # 기존 코드의 'input()' 대신 여기서 상태를 업데이트하며 시작합니다.
    input_message = HumanMessage(content=user_input)

    # 그래프 실행 (resume이 아니라 새로운 입력으로 update)
    # 만약 interrupt 상태에서 멈춰있었다면 Command(resume=...)을 써야 하지만,
    # REST API는 보통 Stateless하므로 매 요청마다 새로운 메시지를 넣는 패턴을 주로 씁니다.

    async def event_generator():
        # 1. 먼저 사용자 메시지를 그래프 상태에 추가하는 과정이 필요할 수 있음
        #    혹은 invoke 시점에 input으로 전달
        async for msg, metadata in graph.astream(
                {"logs": [input_message]},
                config,
                stream_mode="messages"
        ):
            if msg.content:
                # SSE(Server-Sent Events) 포맷이나 단순 텍스트로 전송
                yield msg.content

    return StreamingResponse(event_generator(), media_type="text/plain")

# 헬스 체크
@app.get("/health")
def health_check():
    return {"status": "ok"}