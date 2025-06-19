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
    client_id= os.getenv("REDDIT_CLIENT_ID"),
    client_secret= os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="LangGraphAgent by /u/noel_s"
)

def fetch_reddit_posts(subreddit_name):
    posts = reddit.subreddit(subreddit_name).hot(limit=5)
    
    # List to hold formatted strings for each post
    formatted_posts = []
    
    for p in posts:
        post_string = f"- Title: {p.title}\n  URL: {p.url}"
        
        # Check if the post has selftext (body text)
        if p.selftext:
            # Add the body text, stripping leading/trailing whitespace
            post_string += f"\n-  Body: {p.selftext.strip()}"
        
        formatted_posts.append(post_string)
        
    return "\n\n".join(formatted_posts) # Add an extra newline between posts for better readability

class State(TypedDict):
    topic: str
    subreddits: list[str]
    reddit_posts: list[str]
    chosen_post: str
    post_type: str
    messages: Annotated[list, add_messages]

class NewsScraperAgent:
    def __init__(self, llm):
        self.llm = llm

        graph = StateGraph(State)

        graph.add_node("subreddit", self.find_subreddit)

        graph.add_node("fetch_posts", self.fetch_posts_from_tool)

        graph.add_edge("subreddit", "fetch_posts")

        graph.add_node("evaluate_posts", self.evaluvate_posts)
        
        graph.add_edge("fetch_posts", "evaluate_posts")

        graph.add_node("type", self.choose_type)

        graph.add_edge("evaluate_posts", "type")


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

                ! important the names of the subreddits shouldnt have any prefix like r/ or /r/ or anything else, just the name of the subreddit.
                """,
            ),
            (
                "human",
                f"Find the most relevant subreddits for the topic: {topic}. Please return the names of 5 subreddits.",
            )
        ]
        response = self.llm.invoke(message)
        # print(response.content.splitlines())
        return {"subreddits": response.content.splitlines()}


    def fetch_posts_from_tool(self, state: State):
        subreddits = state["subreddits"]
        all_posts = []

        for subreddit in subreddits:
            posts = fetch_reddit_posts(subreddit)
            all_posts.append(f"🔸 Posts from r/{subreddit}:\n{posts}")

        return {"reddit_posts": all_posts}
    
    def evaluvate_posts(self, state: State):
        posts = state["reddit_posts"]
        topic = state["topic"]
        message = [
            (
                "system",
                f"""
                You are an experienced analyst and professional in the field of {topic}. You will be provided with a list of Reddit posts related to the topic. You are currently given the job to find a specific topic to create a social media post about it.
                Your task is to analyze the posts and find the most relevant and interesting ones that can be used to create a social media post.
                You will be given a list of Reddit posts, each post will be in the format:
                🔸 Posts from r/subreddit_name:
                - Post title: Post URL
                - Post body: Post body (if available)

                Based on the post title and body (if available) you should find the most relevant and interesting posts that can be used to create a fun, informative and enganging social media post.

                You should think in deep about each post and analyze it and you should give each post a score from 1 to 10 based on how relevant and interesting it is to the topic.

                Try to find posts that are more informative, technical, educational, or engaging, and avoid posts that are too generic, low quality, or not related to the topic.

                Try to find posts that are talking about new advancements, innovations, groundbreaking research, or any other interesting and relevant information that can be used to create a social media post.

                 Based on your analysis, you should return a single post from the highly scored posts, each posts title, URL and body in the following format:
                example:
                Title: Post title
                URL: Post URL
                Body: Post body (if available)

                If you cannot find any relevant posts, return an empty string.

                !! Important: You should not return any other text, no formatting, no pointers, just the title and URL of the post. and if you cannot find any relevant posts, return an empty string.
                """,
            ),
            (
                "human",
                f"Analyze the following Reddit posts and find the most relevant and interesting one to create a social media post about the topic: {topic}. Here are the posts:\n\n" + "\n\n".join(state["reddit_posts"]),
            )
        ]
        response = self.llm.invoke(message)
        return {"chosen_post": response.content}

        def choose_type(self, state: State):
            topic = state["topic"]
            chosen_post = state["chosen_post"]
            message = [
                (
                    "system",
                    f"""You are an expert in social media marketing and content creation. Your task is to analyze the chosen post and determine the type of social media post that would be most effective for the topic: {topic}.
                    You should consider the content of the post, the target audience, and the platform where the post will be shared.
                    Based on your analysis, you should return a single type of social media post that would be most effective for the topic.
                    The output should be in this format:
                    example:
                        Type: [type of social media post].

                    !! important do not add any unnecessary text only explain what type of post should be made based on the post and the topic.
                    """,
                ),
                (
                    "human",
                    f"Analyze the chosen post and determine the type of social media post that would be most effective for the topic: {topic}. Here is the chosen post:\n\n{chosen_post}",
                )
            ]
            responce = self.llm.invoke(message)
            return {"post_type": responce.content}
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
    

    # print("\n Top Reddit Posts:")
    # for reddit_posts in result['reddit_posts']:
    #     print(reddit_posts)

    # print("*"*300)

    print("\nChosen Post:")
    print(result['chosen_post'])

    print("\n Chosen Type:")
    print(result['post_type'])

if __name__ == "__main__":
    main()
