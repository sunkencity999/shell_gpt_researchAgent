# Shell GPT Research Agent

A next-generation, autonomous command-line research assistant for deep technical, business, and scientific investigations. This tool orchestrates multi-provider web search, advanced content extraction, and multi-step LLM synthesis—all locally, with robust user experience and privacy.

---

## 🚀 Key Features

- **Local LLM Model Selection & Management**
  - Lists all locally installed Ollama models and lets you choose by number for each session.
  - Supports any model available in your Ollama installation.

- **Multi-Source Web Search**
  - Searches across Google, DuckDuckGo, and Brave for comprehensive results.
  - Retrieves relevant information from multiple sources.

- **Robust Content Extraction**
  - Employs newspaper3k, Playwright, and BeautifulSoup for accurate content extraction.
  - Handles various content formats and structures.

- **Progress Bars and Modern CLI UX**
  - Displays visual progress bars and real-time status updates for a seamless CLI experience.
  - Uses the `rich` library for beautiful, modern CLI feedback.

- **True Information Synthesis**
  - Synthesizes actual information and findings from all sources into a unified, actionable report.
  - Provides more than just a summary review of the information.

- **Automatic Report Saving**
  - Saves all research reports in a dedicated `documents/` folder (git-ignored for privacy).

- **Easy Setup and Launch**
  - Installs dependencies and sets up the Python virtual environment via `install.sh`.
  - Launches the Research Agent via `launch_sgpt_research.sh`.

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sunkencity999/shell_gpt_researchAgent.git
   cd shell_gpt_researchAgent
   ```
2. **Run the installer:**
   ```bash
   ./install.sh
   ```
   This sets up your Python virtual environment, installs dependencies, and helps you configure API keys and Ollama models.
3. **Installer creates the `sgpt-research` command:**
   The installer automatically creates a symlink at `~/.local/bin/sgpt-research` so you can launch the agent from anywhere with:
   ```bash
   sgpt-research
   ```
   > **Note:** Ensure `~/.local/bin` is in your `PATH`. Most systems include this by default. If not, add this to your shell config (e.g. `~/.bashrc` or `~/.zshrc`):
   > ```bash
   > export PATH="$HOME/.local/bin:$PATH"
   > ```
4. **Launch the Research Agent:**
   ```bash
   ./launch_sgpt_research.sh
   # or simply
   sgpt-research
   ```

---

## 🧑‍💻 Usage

1. **Start the agent:**
   ```bash
   ./launch_sgpt_research.sh
   # or just
   sgpt-research
   ```
2. **Select your Ollama model** from the menu (with sizes shown).
3. **Enter your research goal** and optional prompts (audience, tone, improvements).
4. **Watch the progress bars** as the agent plans, searches, extracts, summarizes, and synthesizes.
5. **Find your research report** in the `documents/` folder.

---

## ⚠️ Troubleshooting

- **Ollama Models:** Pull at least one model with `ollama pull <model>` before launching.
- **Google API Keys:** You must add both `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` to your `.env` file for web search (see below).
- **Global command:** The installer creates `sgpt-research` in `~/.local/bin`. If `sgpt-research` is not found after install, ensure `~/.local/bin` is in your `PATH`.

---

## 🔑 Google API Keys for Web Search

To enable Google-powered web search, you need two things:

- **Google Custom Search Engine (CSE) ID**
- **Google API Key**

### 1. Get a Google API Key
- Go to the [Google Cloud Console API Credentials page](https://console.cloud.google.com/apis/credentials).
- Click "Create Credentials" → "API key".
- Copy your new API key.

### 2. Set Up a Google Custom Search Engine (CSE)
- Visit the [Google Custom Search Engine setup page](https://cse.google.com/cse/all).
- Click "Add" to create a new search engine.
- For "Sites to search", enter `www.google.com` to enable full web search (or restrict to specific sites if you wish).
- After creation, find your CSE ID in the control panel.

### 3. Add Both Keys to Your `.env` File
```
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_cse_id
```

---

## 🙏 Credits

- **Created by Christopher Bradford**
- **Special thanks to the creators of [shell-gpt](https://github.com/TheR1D/shell_gpt)**, whose work inspired this research agent.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---
