import os
from typing import Annotated
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

from praw import Reddit  

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

reddit = Reddit(
    client_id="_LSPjQeYkd4oHEoMlDCrXA",
    client_secret="gCesPoI87RZszik2L1pPqm6ImH_RyQ",
    user_agent="LangGraphAgent by /u/noel_s"
)

def fetch_reddit_posts(subreddit_name):
    posts = reddit.subreddit(subreddit_name).hot(limit=5)
    return "\n".join([f"- {p.title}: {p.url}" for p in posts])

class State(TypedDict):
    topic: str
    subreddits: list[str]
    reddit_posts: list[str]
    messages: Annotated[list, add_messages]

class NewsScraperAgent:
    def __init__(self, llm):
        self.llm = llm

        graph = StateGraph(State)

        graph.add_node("subreddit", self.find_subreddit)

        graph.add_node("fetch_posts", self.fetch_posts_from_tool)

        graph.add_edge("subreddit", "fetch_posts")

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
                """,
            ),
            (
                "human",
                f"Find the most relevant subreddits for the topic: {topic}. Please return the names of 5 subreddits.",
            )
        ]
        response = self.llm.invoke(message)
        return {"subreddits": response.content.splitlines()}


    def fetch_posts_from_tool(self, state: State):
        subreddits = state["subreddits"]
        all_posts = []

        for subreddit in subreddits:
            posts = fetch_reddit_posts(subreddit)
            all_posts.append(f"🔸 Posts from r/{subreddit}:\n{posts}")

        return {"reddit_posts": all_posts}


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

    result = agent.graph.invoke({'topic': input("enter topic: ")})
    
    print("\n Subreddits:")
    print(result['subreddits'])

    print("\n Top Reddit Posts:")
    print(result['reddit_posts'])

if __name__ == "__main__":
    main()
