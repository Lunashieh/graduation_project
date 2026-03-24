from pydantic import BaseModel


class GenerationOutput(BaseModel):
    diagram_code: str
    explanation: str
    patch_suggestion: str
    notes: str