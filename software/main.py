from ai import LLM

if __name__ == "__main__":
    while True:
        user_prompt = input("Speak to AI: \n")
        print(LLM(user_prompt))