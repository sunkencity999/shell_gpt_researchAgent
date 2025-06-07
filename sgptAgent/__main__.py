import sys
print(f"[DEBUG] Running __main__ from: {__file__}")
print(f"[DEBUG] sys.path: {sys.path}")
from sgptAgent.agent import ResearchAgent

if __name__ == "__main__":
    import os
    # Clear the terminal screen before printing the banner
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    print("\nShell GPT Research Agent\n========================\n")
    try:
        # List installed Ollama models
        import subprocess
        import re
        models = []
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # skip header
                fields = re.split(r'\s{2,}', line.strip())
                # fields: NAME, ID, SIZE, MODIFIED
                if len(fields) >= 3:
                    name = fields[0]
                    size = fields[2]
                    models.append({'name': name, 'size': size})
        except Exception as e:
            print("[ERROR] Could not list Ollama models:", e)
            models = []
        if not models:
            print("No Ollama models found. Please run 'ollama pull <model>' first.")
            exit(1)
        print("\nAvailable Ollama Models:")
        for idx, m in enumerate(models, 1):
            print(f"  {idx}. {m['name']}  [size: {m['size']}]" )
        selected = None
        while selected is None:
            choice = input(f"\nSelect a model by number (1-{len(models)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                selected = models[int(choice)-1]['name']
            else:
                print("Invalid selection. Please enter a valid number.")
        model = selected
        # Prompt for all fields in sequence, only proceed when all are collected
        goal = ""
        while not goal:
            goal = input("Enter your research goal: ").strip()
            if not goal:
                print("Please enter a research goal.")
        audience = input("Who is the intended audience? (e.g., C-suite, technical, general): ").strip()
        tone = input("Preferred tone/style? (e.g., formal, technical, accessible): ").strip()
        improvement = input("Anything specific to improve with the summary? (optional): ").strip()
        agent = ResearchAgent(model=model)
        agent.run(goal, audience=audience, tone=tone, improvement=improvement)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
