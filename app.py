import json
import os
import streamlit as st
import instructor
from llama_cpp import Llama
from pydantic import BaseModel, Field
from typing import List, Optional

# Import the deck builder from your existing script
from build_deck import create_deck

# ---------------------------------------------------------
# Pydantic Schema Definitions
# ---------------------------------------------------------
class HardwareItem(BaseModel):
    name: str = Field(description="Full exact name of component or part (e.g. 'Arduino Uno', 'L298N Motor Driver', 'HC-SR04 Sensor')")
    category: str = Field(description="Must be one of: 'Electronic', 'Mechanical/Structural', or 'Fasteners/Tools'")
    quantity: int = Field(description="Quantity needed")
    estimated_cost_usd: float = Field(description="Approximate cost in USD")
    sourcing_method: str = Field(description="How to acquire or make it (e.g. '3D Print (PLA, 20% infill)', 'Buy Off-the-Shelf', 'Hardware Store')")
    notes: Optional[str] = Field(default=None, description="Specifications, search queries, or mounting notes")

class PinConnection(BaseModel):
    from_component: str = Field(description="Exact source component name matching hardware list (e.g. 'HC-SR04 Ultrasonic Sensor')")
    from_pin: str = Field(description="Pin/terminal on source component (e.g. 'Trig', 'OUT1', 'VCC')")
    to_component: str = Field(description="Exact target component name matching hardware list (e.g. 'Arduino Uno', 'DC Motor Left')")
    to_pin: str = Field(description="Pin/terminal on target component (e.g. 'Pin 9', 'Positive Terminal', '5V')")
    wire_purpose: Optional[str] = Field(default=None, description="Signal type or wire color (e.g., 'PWM Control Signal', '5V Power', 'Ground')")

class CodeFile(BaseModel):
    filename: str = Field(description="File name")
    language: str = Field(description="Programming language")
    code: str = Field(description="Full compilable code snippet")

class AssemblyStep(BaseModel):
    step_number: int
    title: str
    description: str
    safety_warning: Optional[str] = None

class RoboticsGuide(BaseModel):
    project_title: str
    summary: str
    difficulty_level: str
    hardware: List[HardwareItem]
    wiring: List[PinConnection]
    code_files: List[CodeFile]
    steps: List[AssemblyStep]

# ---------------------------------------------------------
# Cache Model Loading (Loads into RAM only ONCE)
# ---------------------------------------------------------
@st.cache_resource
def load_llm_engine():
    llama = Llama(
        model_path="./models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
        n_ctx=4096,
        verbose=False
    )
    return instructor.patch(
        create=llama.create_chat_completion_openai_v1,
        mode=instructor.Mode.MD_JSON,
    )

# ---------------------------------------------------------
# Streamlit Page Setup & Custom CSS
# ---------------------------------------------------------
st.set_page_config(page_title="AI Robotics Mentor", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* Main Canvas Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Hero Banner Container */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.8rem;
        border-left: 6px solid #0EA5E9;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #0EA5E9;
        font-weight: 500;
    }
    
    /* Cards and Metric Overrides */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #0EA5E9;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Controls & System Status
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ System Status")
    st.success("🟢 Local LLM Engine: Active")
    st.info("📦 Graphviz Engine: Loaded")
    st.divider()
    
    st.header("🎛️ Generation Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05, help="Lower values yield strict adherence to schemas.")
    max_tokens = st.number_input("Max Tokens", 512, 4096, 2048, step=256)
    st.caption("All generations are executed 100% locally on your hardware.")

# ---------------------------------------------------------
# Hero Banner & Metrics Header
# ---------------------------------------------------------
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🤖 Local AI Robotics Mentor</div>
        <div class="hero-subtitle">Architect hardware schematics, physical CAD links, assembly steps, and PowerPoint decks offline.</div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Interactive Quick-Start Prompt Pills
# ---------------------------------------------------------
st.markdown("**💡 Quick-Start Project Templates:**")

if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = "I want to build a simple two-wheeled obstacle avoiding robot using Arduino."

c1, c2, c3 = st.columns(3)

if c1.button("🤖 2-DOF Robotic Arm", use_container_width=True):
    st.session_state.prompt_text = "Build a 2 DOF robotic arm using SG90 servos, Arduino Uno, 3D printed links, and M3 hardware."

if c2.button("🚗 Obstacle Avoidance Rover", use_container_width=True):
    st.session_state.prompt_text = "Build a 2-wheeled obstacle avoiding robot chassis with an L298N driver and HC-SR04 ultrasonic sensor."

if c3.button("🌡️ IoT Weather Station", use_container_width=True):
    st.session_state.prompt_text = "Build an IoT mini weather station using ESP32, DHT22 temp sensor, 3D printed enclosure, and an OLED display."

prompt_input = st.text_area(
    "Describe the robotics project you want to build:",
    key="prompt_text",
    height=100
)

# ---------------------------------------------------------
# System Instructions for Llama
# ---------------------------------------------------------
SYSTEM_INSTRUCTIONS = (
    "You are a senior robotics mentor. Output ONLY raw JSON matching the target schema.\n\n"
    "CRITICAL REQUIREMENT FOR HARDWARE:\n"
    "You MUST provide a complete Bill of Materials covering BOTH electronics AND physical structural parts.\n"
    "Categorize items as 'Electronic', 'Mechanical/Structural', or 'Fasteners/Tools'.\n\n"
    "CRITICAL RULES FOR WIRING CONNECTIONS:\n"
    "1. Exact Component Names: 'from_component' and 'to_component' MUST use exact names from the hardware list.\n"
    "2. No Self-Loops or Controller Aliases: Never connect a microcontroller to itself or to an alias (e.g., NEVER 'Arduino' to 'Microcontroller').\n"
    "3. Complete End-to-End Connections: You MUST include:\n"
    "   - Power/GND rails (e.g. Battery -> Motor Driver VCC, Arduino 5V -> Sensor VCC).\n"
    "   - Control Signals (e.g. Sensor output -> Arduino Digital Input, Arduino PWM -> Motor Driver Input).\n"
    "   - Actuator Outputs (e.g. Motor Driver OUT1/OUT2 -> DC Motor Terminals).\n"
    "4. Do NOT omit high-current paths like Motor Driver to Motors."
)

# ---------------------------------------------------------
# Generation Pipeline
# ---------------------------------------------------------
if st.button("Generate Complete Project Deck", type="primary", use_container_width=True):
    with st.spinner("Analyzing prompt and generating structured guide (~5-15mins)..."):
        client = load_llm_engine()
        
        guide: RoboticsGuide = client(
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt_input}
            ],
            response_model=RoboticsGuide,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"}
        )

        # Save JSON
        json_data = guide.model_dump()
        with open("latest_guide.json", "w") as f:
            json.dump(json_data, f, indent=2)

        # Render presentation using updated build_deck script
        create_deck("latest_guide.json", "robotics_guide.pptx")

    st.success("Project guide and PowerPoint deck generated successfully!")

    # Display summary tab UI
    st.header(guide.project_title)
    st.caption(f"Difficulty Level: {guide.difficulty_level}")
    st.write(guide.summary)

    tab1, tab2, tab3, tab4 = st.tabs(["🔩 Bill of Materials", "🔌 Wiring Pinout", "🛠️ Assembly Steps", "💻 Source Code"])

    with tab1:
        st.table([h.model_dump() for h in guide.hardware])

    with tab2:
        st.table([w.model_dump() for w in guide.wiring])

    with tab3:
        for step in guide.steps:
            st.markdown(f"**Step {step.step_number}: {step.title}**")
            st.write(step.description)
            if step.safety_warning:
                st.warning(step.safety_warning)

    with tab4:
        for code_f in guide.code_files:
            st.markdown(f"**{code_f.filename}** ({code_f.language})")
            st.code(code_f.code, language=code_f.language.lower())

    # Direct File Download Button
    with open("robotics_guide.pptx", "rb") as pptx_file:
        st.download_button(
            label="📥 Download Presentation (.pptx)",
            data=pptx_file,
            file_name=f"{guide.project_title.lower().replace(' ', '_')}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True
        )