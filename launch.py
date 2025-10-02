from controller import Controller
from retriever import Retriever
from ontology import Ontology
from config import API_KEY

ctrl = Controller(api_key=API_KEY)
retriever = Retriever()
ontology = Ontology()

def main():
    while True:
        prompt = input("🧠 AgentOS > ")
        if prompt.startswith("search:"):
            keyword = prompt.split("search:")[1].strip()
            results = retriever.search(keyword)
            for r in results:
                print(f"[{r[0]}] {r[1]} → {r[2]}")
        elif prompt.startswith("define:"):
            parts = prompt.split("define:")[1].strip().split("=")
            ontology.define(parts[0].strip(), {"description": parts[1].strip()})
            print(f"✅ Defined {parts[0].strip()}")
        elif prompt == "exit":
            break
        else:
            response = ctrl.run(prompt)
            print(f"🤖 {response}")

if __name__ == "__main__":
    main()

