"""Pydantic models for request/response validation"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class QuestionRequest(BaseModel):
    """Request model for asking a question"""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's question about the election process"
    )

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean question input"""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty")
        if len(cleaned) < 2:
            raise ValueError("Question is too short to process")
        return cleaned


class QuestionResponse(BaseModel):
    """Response model for election information"""

    category: str = Field(..., description="Detected intent category")
    title: str = Field(..., description="Response title")
    overview: str = Field(..., description="Brief overview of the topic")
    steps: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    documents: List[str] = Field(default_factory=list, description="Required documents")
    tips: List[str] = Field(default_factory=list, description="Helpful tips")
    next_action: str = Field(default="", description="Recommended next action")
    matched_keywords: int = Field(default=0, description="Number of keywords matched for intent detection")
    confidence: str = Field(default="low", description="Detection confidence: high, medium, or low")
    confidence_reason: str = Field(
        default="",
        description="Short explanation of why the confidence level was assigned"
    )
    intent_reason: str = Field(
        default="",
        description="Human-readable explanation of why this intent was selected"
    )
    system_mode: str = Field(
        default="fallback",
        description="Content source mode for this response: sheets, gcs, or fallback"
    )
    served_from_cache: bool = Field(
        default=False,
        description="Whether this response was served from in-memory cache"
    )
    data_source_note: str = Field(
        default="",
        description="Human-readable note about the active data source"
    )


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str = Field(..., description="System status")
    mode: str = Field(..., description="Operating mode: sheets or fallback")
    timestamp: str = Field(..., description="Current UTC timestamp")

    @classmethod
    def create(cls, mode: str) -> "HealthResponse":
        """Create a health response with current timestamp"""
        return cls(
            status="healthy",
            mode=mode,
            timestamp=datetime.now(timezone.utc).isoformat()
        )


class CategoriesResponse(BaseModel):
    """Response model for supported categories"""

    categories: List[str] = Field(..., description="List of supported intent categories")

    @classmethod
    def create(cls, categories: List[str]) -> "CategoriesResponse":
        """Create a categories response"""
        return cls(categories=categories)


class DebugSourceResponse(BaseModel):
    """Response model for debug/source endpoint"""

    content_source: str = Field(..., description="Active content source: sheets, gcs, or fallback")
    cache_loaded: bool = Field(..., description="Whether cache is populated")
    fallback_active: bool = Field(..., description="Whether fallback mode is active")
    cache_size: int = Field(..., description="Number of categories in cache")
    app_version: str = Field(..., description="Application version")
    sheets_configured: bool = Field(..., description="Whether SHEET_ID is set in environment")
    sheet_name: str = Field(default="", description="Configured worksheet name (safe to expose)")
    access_mode: str = Field(default="", description="Configured Sheets access mode")
    demo_sheet_ready: bool = Field(default=False, description="True when SHEET_ID is configured")
    gcs_configured: bool = Field(default=False, description="Whether GCS_CONTENT_URL is set")
    gcs_loaded: bool = Field(default=False, description="Whether GCS content was loaded successfully")
    gcs_available: bool = Field(default=False, description="Whether GCS is configured and loaded")
    sheets_repaired_rows: int = Field(default=0, description="Number of rows auto-repaired during Sheets load")
    google_services_used: List[str] = Field(
        default_factory=list,
        description="List of Google services actively used by this deployment"
    )

