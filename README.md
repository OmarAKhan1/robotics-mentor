# 🤖 Local AI Robotics Mentor

An offline, AI system that takes a user's proposed robotics project and generates a PowerPoint presentation deck with structured hardware schematics, Bill of Materials (BOM), assembly steps, code needed to construct said project.

---

## 📋 System Requirements

* **OS:** Linux (Ubuntu/Debian recommended), macOS, or Windows (WSL2)
* **Python:** 3.10 or 3.11
**Python:** 8GB or more
---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME
```

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🧠 Download Model Weights

1. Create a `models` directory in the root folder:
   ```bash
   mkdir -p models
   ```
2. Download the Qwen2.5 7B Instruct GGUF model (`qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf`) from HuggingFace.
3. Move the downloaded `.gguf` file into the `./models/` directory:
   ```text
   YOUR_REPOSITORY_NAME/
   ├── models/
   │   └── qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
   ├── app.py
   ├── build_deck.py
   └── README.md
   ```

---

## 🚀 Running the App

Launch the Streamlit interface:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📁 Output Artifacts

* **JSON Guide:** Saved automatically to `latest_guide.json`.
* **PowerPoint Presentation:** Generated as `robotics_guide.pptx` and downloadable directly from the UI.
