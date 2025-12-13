# 🚀 Stratabid: The Agentic RFP Engine

### Autonomous B2B Tender Automation with "Fail-Safe" Intelligence
**Eliminating "Silent Failures" in Industrial Bids using Multi-Agent Orchestration.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![AI](https://img.shields.io/badge/AI-Multi--Agent-purple)
![Status](https://img.shields.io/badge/Status-Prototype-green)

---

## 📋 Executive Summary
**Stratabid** (formerly Project TenderOS) is an Agentic AI system designed to automate the processing of complex B2B Requests for Proposals (RFPs), specifically for the Wires & Cables industry. 

Unlike standard GenAI wrappers that hallucinate prices or specifications, Stratabid uses a **Hybrid Architecture** combining **Vector Search (Semantic)** with **Rule-Based Scoring (Engineering Strictness)**. It autonomously parses RFPs, matches SKUs, calculates pricing against real-time inventory, and validates safety rules—reducing bid turnaround time by **80%** while ensuring 100% technical compliance.

---

## 🛑 The Problem
In industrial B2B sales, responding to a tender is a slow, linear, and risky process:
1.  **Manual Discovery:** Sales engineers waste hours reading 100+ page PDFs.
2.  **"Silent Failures":** AI tools often hallucinate substitutes (e.g., matching *Aluminum* when *Copper* is requested), leading to catastrophic financial losses.
3.  **Inventory Disconnect:** Bids are often won on paper but fail in execution because the inventory wasn't checked during the pricing phase.

## 💡 The Solution: Agentic Orchestration
We replaced the linear manual workflow with a parallel **Team of Agents**:

| Agent | Role | Function |
| :--- | :--- | :--- |
| **🕵️ Sales Agent** | **Parser** | Uses Regex & NLP "Strict Mode" to extract Voltage, Material, and Cores without hallucination. |
| **🧠 Technical Agent** | **Engineer** | Performs **Hybrid Matching**: Vector Search for discovery + Weighted Logic (35% Voltage, 30% Material) for ranking. |
| **💰 Pricing Agent** | **Controller** | Calculates commercial margins and checks **Real-Time Inventory** availability. |
| **🛡️ Decision Agent** | **Auditor** | The "Fail-Safe" layer. Decides if a bid is **Auto-Approved**, **Rejected**, or needs **Manual Review**. |

---

## 🏗️ Architecture
*(Place your generated architecture image here, e.g., assets/architecture.png)*

The system operates on a **Hub-and-Spoke model** governed by a Main Orchestrator.
1.  **Input:** Unstructured Text/JSON from RFP.
2.  **Process:** Parallel execution of Technical and Pricing agents.
3.  **Logic:** Proximity Scoring (e.g., 33kV is a valid substitute for 30kV, but 1.1kV is not).
4.  **Output:** Final Bid Package with audit logs.

---

## ⚙️ Key Features
* **Hybrid Search Engine:** Combines FAISS (Vector DB) for finding candidates and Python-based logic for scoring them.
* **"Strict Mode" Parsing:** If the RFP asks for "Nickel" and it's not in the DB, the score defaults to 0.0 (Manual Review) instead of guessing "Aluminum".
* **Weighted Scoring Model:**
    * Voltage: 35% (Critical Safety)
    * Material: 30% (Critical Cost)
    * Cores: 20%
* **Inventory Awareness:** A bid is only Auto-Approved if `Stock_Available >= Required_Quantity`. Otherwise, it flags for production review.

---

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **Frontend:** Streamlit (Web Dashboard)
* **LLM/NLP:** Google Gemini / OpenAI (for parsing), Sentence-Transformers (for Embeddings)
* **Vector Database:** FAISS (Facebook AI Similarity Search)
* **Data Processing:** Pandas, NumPy, Regex

---

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/stratabid.git](https://github.com/yourusername/stratabid.git)
    cd stratabid
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables**
    Create a `.env` file and add your API Key:
    ```bash
    GEMINI_API_KEY="your_api_key_here"
    ```

5.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

---

## 📸 Usage Guide
1.  **Launch the App:** Open the localhost link provided by Streamlit.
2.  **Paste RFP Data:** Use the sidebar to paste raw text or JSON (e.g., `{"Voltage": 1.1, "Material": "Copper"...}`).
3.  **Click "Analyze RFP":** Watch the Agents initialize and process in real-time.
4.  **Review Output:**
    * **Green:** ✅ Auto-Approved (High Score + In Stock).
    * **Yellow:** ⚠️ Manual Review (Inventory Low or Score < 90%).
    * **Red:** 🛑 Rejected (Technical Mismatch).

---

## 🔮 Future Roadmap (TenderOS™)
* **Universal Ingestion:** OCR integration for parsing Engineering Drawings and scanned PDFs.
* **RLHF Feedback Loop:** A Feedback Agent that learns from human overrides to improve scoring weights.
* **Supply Chain Bot:** Autonomous RFQ generation to sub-suppliers when stock is low.
* **LME Integration:** Real-time London Metal Exchange pricing for dynamic commodity hedging.

---

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
