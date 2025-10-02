from agent import Agent
from memory import Memory
from retriever import Retriever
from config import API_KEY

class Controller:
    def __init__(self, api_key=API_KEY):
        self.agent = Agent(api_key)
        self.memory = Memory()
        self.retriever = Retriever()

    def run(self, prompt):
        response = self.agent.query(prompt)
        self.memory.log(prompt, response)
        return response

