import os
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class State(TypedDict):
    topic: str
    subreddits: list[str]
    messages: Annotated[list, add_messages]


class NewsScraperAgent:
    def __init__(self, llm):
        self.llm = llm
        
        # Graph definition
        graph = StateGraph(State)
        graph.add_node("subreddit", self.find_subreddit)
        graph.set_entry_point("subreddit")
        self.graph = graph.compile()

    def find_subreddit(self, state: State):
        topic = state["topic"]
        message = [
            (
                "system",
                """You are an agent that knows most subreddits and what each subreddit is about. Your task is given a topic, to find the most relevant subreddit and return the names of 5 those subreddits.
                Make Sure to only return the names of the subreddits, no other text, no formatting, no pointers. If you cannot find any relevant subreddit, return an empty list.
                The output should be in this format:
                example:
                    subreddit1
                    subreddit2
                    subreddit3
                    .
                    .
                """,
            ),
            (
                "human",
                f"Find the most relevant subreddits for the topic: {topic}. Please return the names of 5 subreddits.",
            )
        ]
        responce = self.llm.invoke(message)
        return {"subreddits": responce.content.splitlines()}
    
    def get_top_k_posts(self, state: State):
        subreddits = state["subreddits"]
        
    

def main():
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    agent = NewsScraperAgent(model)
    result = agent.graph.invoke({'topic': 'LLM'})
    print(result['subreddits'])

if __name__ == "__main__":
    main()