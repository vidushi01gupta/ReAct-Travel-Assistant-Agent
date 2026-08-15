# ✈️ ReAct Travel Assistant

An AI-powered travel assistant that uses a **ReAct agent** to search and combine real-time travel information from multiple services.

##  Features

*  Flight search
*  Train search
*  Bus search
*  Hotel search
*  Weather information
*  Estimated trip cost
*  ReAct agent using LangGraph
*  Multiple conversation history
*  Source/booking links when available

## 🛠️ Tech Stack

* **Python**
* **LangChain**
* **LangGraph**
* **Groq**
* **Streamlit**
* **REST APIs**

##  How It Works

```text
User
 ↓
Streamlit Chat Interface
 ↓
ReAct AI Agent
 ↓
Selects Required Tools
 ↓
Flights / Trains / Buses / Hotels / Weather
 ↓
Combines Results
 ↓
Personalized Trip Plan
```

##  Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/vidushi01gupta/ReAct-Travel-Assistant-Agent.git
cd ReAct-Travel-Assistant-Agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will open at:

```text
http://localhost:8501
```

##  Example Query

```text
Plan a trip from Delhi to Goa from 20 August 2026
to 23 August 2026. Find flights, trains, buses,
hotels, weather and estimate the total trip cost.
```

The agent selects the required tools, collects the available information, and presents the results in one response.

##  Project Structure

```text
ReAct-Travel-Assistant-Agent/
│
├── app.py
├── travel_assistant.py
├── main.py
├── travel_assistant.ipynb
├── requirements.txt
├── pyproject.toml
├── README.md
├── .gitignore
└── .env
```


##  Note

Travel information depends on the external APIs being used. Availability, prices, schedules, and weather data may change or may be unavailable due to API limits or provider restrictions.

## 👩‍💻 Author

**Vidushi Gupta**

GitHub:
https://github.com/vidushi01gupta
