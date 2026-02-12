import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from my_agent.agent import root_agent


async def generate_answer(question: str) -> str:
    """Generate answer using Google ADK agent (agent will search as needed)"""
    try:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="naive_rag",
            session_service=session_service
        )
        session = await session_service.create_session(
            app_name="naive_rag",
            user_id="user"
        )

        final_response = ""
        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=types.UserContent(question)
        ):
            # Only capture the final response, skip thinking/intermediate events
            if not event.is_final_response():
                continue
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response += part.text

        return final_response if final_response else "No response generated."
    except Exception as e:
        return f"Error generating answer: {e}"


async def ask_question(question: str) -> str:
    """Main RAG pipeline - agent handles search via tool"""
    print("  → Sending question to agent...")
    answer = await generate_answer(question)
    return answer


# For standalone testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python query.py <your question>")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"\nQuestion: {question}\n")
    answer = asyncio.run(ask_question(question))
    print(f"Answer: {answer}\n")
