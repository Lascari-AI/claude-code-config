from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

# ═══════════════════════════════════════════════════════════
# API REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class AutocompleteItem(BaseModel):
    """Single autocomplete suggestion"""
    completion: str
    reasoning: str

class AutocompleteGenerateRequest(BaseModel):
    """Request to generate autocomplete suggestions"""
    user_input: str
    orchestrator_agent_id: str

class AutocompleteResponse(BaseModel):
    """Response containing autocomplete suggestions"""
    status: str = "success"
    autocompletes: List[AutocompleteItem]
    total_items: int
    orchestrator_agent_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AutocompleteUpdateRequest(BaseModel):
    """Request to update completion history"""
    orchestrator_agent_id: str
    completion_type: Literal['none', 'autocomplete']
    user_input_on_enter: Optional[str] = None
    user_input_before_completion: Optional[str] = None
    autocomplete_item: Optional[str] = None
    reasoning: Optional[str] = None

    @model_validator(mode='after')
    def validate_fields(self):
        if self.completion_type == 'none' and not self.user_input_on_enter:
            raise ValueError("user_input_on_enter required for type 'none'")
        if self.completion_type == 'autocomplete':
            if not all([self.user_input_before_completion, self.autocomplete_item, self.reasoning]):
                raise ValueError("All autocomplete fields required")
        return self

# ═══════════════════════════════════════════════════════════
# EXPERTISE.YAML STRUCTURE MODELS (Type Safety)
# ═══════════════════════════════════════════════════════════

class PreviousCompletionNone(BaseModel):
    """
    Completion event where user typed manually (didn't accept autocomplete).

    Maps to expertise.yaml structure when completion_type='none'
    """
    completion_type: Literal['none']
    user_input_on_enter: str = Field(..., description="Full user input when Enter was pressed")
    order: int = Field(..., description="Sequential order of this completion event")

    class Config:
        frozen = False  # Allow updates if needed

class PreviousCompletionAutocomplete(BaseModel):
    """
    Completion event where user accepted an autocomplete suggestion.

    Maps to expertise.yaml structure when completion_type='autocomplete'
    """
    completion_type: Literal['autocomplete']
    user_input_before_completion: str = Field(..., description="User input before autocomplete was applied")
    autocomplete_item: str = Field(..., description="The autocomplete text that was accepted")
    reasoning: str = Field(..., description="Why this autocomplete was suggested")
    order: int = Field(..., description="Sequential order of this completion event")

    class Config:
        frozen = False  # Allow updates if needed

# Union type for previous_completions list items
PreviousCompletion = Union[PreviousCompletionNone, PreviousCompletionAutocomplete]

class AutocompleteExpertiseData(BaseModel):
    """
    CRITICAL: Type-safe model for entire expertise.yaml structure.

    This model ensures type safety when loading/saving expertise.yaml.
    All access to expertise_data should go through this model.

    Fields:
        orchestrator_agent_id: Current orchestrator UUID (triggers reset if changed)
        completion_agent_id: Claude Agent SDK session_id (None until first interaction)
        previous_completions: List of completion events (union type)
    """
    orchestrator_agent_id: str = Field(..., description="Current orchestrator UUID")
    completion_agent_id: Optional[str] = Field(
        None,
        description="Claude Agent SDK session_id (captured after first interaction)"
    )
    previous_completions: List[PreviousCompletion] = Field(
        default_factory=list,
        description="History of completion events (union of 'none' and 'autocomplete' types)"
    )

    class Config:
        frozen = False  # Allow mutations during runtime

    def to_dict(self) -> dict:
        """Convert to dict for YAML serialization"""
        return self.model_dump(mode='python', exclude_none=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'AutocompleteExpertiseData':
        """Load from dict (YAML data) with validation"""
        return cls(**data)
