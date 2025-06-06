from .agent import ResearchAgent

if __name__ == "__main__":
    print("\nShell GPT Research Agent\n========================\n")
    try:
        goal = input("Enter your research goal: ").strip()
        if not goal:
            print("No research goal entered. Exiting.")
        else:
            agent = ResearchAgent()
            agent.run(goal)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
