from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict
from business.usecase.agentic.agentic_usecase import AgenticUsecase
from haystack.dataclasses import ChatMessage
from copy import deepcopy
import asyncio
import time

router = APIRouter(prefix="/agentic/v1/chat", tags=["Agentic Chat"])

# Session store for chat history and metadata
# Each session_id maps to a dict: {"history": List[ChatMessage], "tokens": Dict, "last_access": timestamp}
session_store: Dict[str, Dict] = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutes


# Dependency injection
def get_usecase() -> AgenticUsecase:
    return AgenticUsecase()


# Helper: clean expired sessions
def clean_expired_sessions():
    now = time.time()
    expired_sessions = [sid for sid, data in session_store.items() if now - data["last_access"] > SESSION_TIMEOUT]
    for sid in expired_sessions:
        del session_store[sid]


# Streaming generator
async def stream_generator(user_query: str, usecase: AgenticUsecase, session_id: str):
    clean_expired_sessions()
    queue: asyncio.Queue = asyncio.Queue()

    session_data = session_store.setdefault(session_id, {"history": [], "tokens": {}, "last_access": time.time()})
    session_data["last_access"] = time.time()

    # Callback pushes text to queue
    def streaming_callback(chunk):
        """
        Build the full chunk text like collect_streaming_chunk,
        then push it to the queue for streaming.
        """
        chunk_text = ""

        if chunk.start and chunk.index and chunk.index > 0:
            chunk_text += "\n\n"

        # Tool calls
        if chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                if chunk.start:
                    if chunk.index and tool_call.index > chunk.index:
                        chunk_text += "\n\n"
                    chunk_text += f"[TOOL CALL]\nTool: {tool_call.tool_name} \nArguments: "
                if tool_call.arguments:
                    chunk_text += str(tool_call.arguments)

        # Tool call result
        if chunk.tool_call_result:
            chunk_text += f"[TOOL RESULT]\n{chunk.tool_call_result.result}"

        # Normal assistant content
        if chunk.content:
            if chunk.start:
                chunk_text += "[ASSISTANT]\n"
            chunk_text += chunk.content

        # Reasoning content
        if chunk.reasoning:
            if chunk.start:
                chunk_text += "[REASONING]\n"
            chunk_text += chunk.reasoning.reasoning_text

        if chunk.finish_reason is not None:
            chunk_text += "\n\n"

        # Append to usecase answer_stream
        usecase.answer_stream += chunk_text

        # Push chunk_text to the queue for streaming
        if chunk_text:
            queue.put_nowait(chunk_text.encode("utf-8"))



    # Run blocking execute() in thread pool
    loop = asyncio.get_event_loop()
    execute_task = loop.run_in_executor(
        None,
        lambda: usecase.execute(user_query=user_query, chat_history=deepcopy(session_data["history"]), streaming_callback=streaming_callback)
    )

    

    # Stream from queue while execute() is running
    while True:
        try:
            chunk = queue.get_nowait()
            yield chunk
        except asyncio.QueueEmpty:
            if execute_task.done():
                break
            await asyncio.sleep(0.05)  # small delay to allow new chunks

    # Drain any remaining items
    while not queue.empty():
        yield queue.get_nowait()
    
    final_answer = usecase.answer_stream.strip()
    if final_answer:
        session_data["history"].append(ChatMessage.from_user(user_query))
        session_data["history"].append(ChatMessage.from_assistant(final_answer))
    
    if execute_task.done():
        session_data["tokens"] = execute_task.result().get("tokens_used", {}) # type: ignore
    




# API endpoint: streaming chat
@router.post("/")
async def chat_agentic(user_query: str, session_id: str, usecase: AgenticUsecase = Depends(get_usecase)):
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return StreamingResponse(
        stream_generator(user_query, usecase, session_id),
        media_type="application/json"
    )


# API endpoint: get chat history
@router.get("/history")
async def get_chat_history(session_id: str):
    clean_expired_sessions()
    session_data = session_store.get(session_id)
    if not session_data:
        return JSONResponse(content={"history": []})
    # Return serialized chat history
    return JSONResponse(content={
        "history": [{"role": msg.role, "content": msg.text} for msg in session_data["history"]]
    })


# API endpoint: get tokens used
@router.get("/tokens")
async def get_tokens(session_id: str):
    clean_expired_sessions()
    session_data = session_store.get(session_id)
    if not session_data:
        return JSONResponse(content={"tokens": {}})
    return JSONResponse(content={"tokens": session_data.get("tokens", {})})
