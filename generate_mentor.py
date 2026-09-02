import json
from typing import List, Optional
from pydantic import BaseModel, Field
import instructor
from llama_cpp import Llama

# ---------------------------------------------------------
# 1. Define Structured Data Schema (Pydantic)
# ---------------------------------------------------------
class HardwareItem(BaseModel):
    name: str = Field(description="Component name, e.g., Arduino Uno R3")
    quantity: int = Field(description="Quantity needed")
    estimated_cost_usd: float = Field(description="Approximate cost in USD")
    notes: Optional[str] = Field(default=None, description="Operating voltage or specifications")

class PinConnection(BaseModel):
    component: str = Field(description="Source component, e.g., HC-SR04")
    from_pin: str = Field(description="Pin on source component, e.g., Trig")
    to_pin: str = Field(description="Target pin on microcontroller, e.g., D9")

class CodeFile(BaseModel):
    filename: str = Field(description="File name, e.g., main.ino")
    language: str = Field(description="Programming language, e.g., C++")
    code: str = Field(description="Full compilable code snippet")

class AssemblyStep(BaseModel):
    step_number: int
    title: str
    description: str
    safety_warning: Optional[str] = None

class RoboticsGuide(BaseModel):
    project_title: str
    summary: str
    difficulty_level: str = Field(description="Beginner, Intermediate, or Advanced")
    hardware: List[HardwareItem]
    wiring: List[PinConnection]
    code_files: List[CodeFile]
    steps: List[AssemblyStep]

# ---------------------------------------------------------
# 2. Initialize Local LLM & Instructor Engine
# ---------------------------------------------------------
print("Loading model into memory...")
llama = Llama(
    model_path="./models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
    n_ctx=4096,
    verbose=False
)

# Patch llama-cpp-python using Mode.MD_JSON to handle local model backticks
create = instructor.patch(
    create=llama.create_chat_completion_openai_v1,
    mode=instructor.Mode.MD_JSON,
)

# ---------------------------------------------------------
# 3. Request Guide Generation
# ---------------------------------------------------------
prompt = "I want to build a simple two-wheeled obstacle avoiding robot using Arduino."

print("Generating structured robotics guide...")
guide: RoboticsGuide = create(
    messages=[
        {
            "role": "system",
            "content": (
                "You are a senior robotics mentor. Output ONLY raw JSON matching the target schema. "
                "Do NOT wrap the response in top-level object keys or markdown conversational fluff."
            )
        },
        {"role": "user", "content": prompt}
    ],
    response_model=RoboticsGuide,
    max_tokens=2048,
    temperature=0.1,
    response_format={"type": "json_object"}
)

# ---------------------------------------------------------
# 4. Output / Save Results
# ---------------------------------------------------------
print("\n=== GENERATION SUCCESSFUL ===")
print(f"Title: {guide.project_title}")
print(f"Difficulty: {guide.difficulty_level}")
print(f"Components required: {len(guide.hardware)}")
print(f"Wiring connections: {len(guide.wiring)}")

with open("latest_guide.json", "w") as f:
    json.dump(guide.model_dump(), f, indent=2)

print("Saved structured output to 'latest_guide.json'.")