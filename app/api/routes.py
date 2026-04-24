"""API routes for VotePath AI Backend"""

import logging
from fastapi import APIRouter
from app.models.schemas import (
    QuestionRequest,
    QuestionResponse,
    HealthResponse,
    CategoriesResponse,
    DebugSourceResponse,
)
from app.services.intent_service import (
    detect_intent_with_metadata,
    get_matched_keyword_names,
    build_intent_reason,
    build_confidence_reason,
    get_supported_intents,
    OUT_OF_SCOPE_DATA,
)
from app.services.response_service import ResponseService
from app.services.fallback_service import FallbackService
from app.utils.cache import get_cache
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
response_service = ResponseService()
fallback_service = FallbackService()


@router.get("/", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns system status and current operating mode (sheets or fallback).
    """
    try:
        cache = get_cache()
        mode = "sheets" if cache.size() > 0 else "fallback"
        logger.debug("Health check requested — mode: %s", mode)
        return HealthResponse.create(mode=mode)
    except Exception as exc:
        logger.error("Health check error: %s", exc)
        return HealthResponse.create(mode="fallback")


@router.get("/categories", response_model=CategoriesResponse, summary="List supported categories")
async def get_categories() -> CategoriesResponse:
    """
    Return all supported intent categories.

    Clients can use this list to build quick-action buttons in the UI.
    """
    try:
        categories = get_supported_intents()
        return CategoriesResponse.create(categories=categories)
    except Exception as exc:
        logger.error("Error fetching categories: %s", exc)
        return CategoriesResponse.create(categories=["faq"])


@router.post("/ask", response_model=QuestionResponse, summary="Ask an election question")
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Process a user question and return a structured election-guidance response.

    The system detects the user's intent via keyword matching, retrieves the
    relevant content from cache (populated from Google Sheets or fallback data),
    and returns a structured response with steps, documents, tips, and a next action.
    """
    try:
        # Step 1: Detect intent with metadata
        intent, matched_keywords, confidence = detect_intent_with_metadata(request.question)
        matched_kw_names = get_matched_keyword_names(request.question, intent)
        intent_reason = build_intent_reason(intent, matched_kw_names)
        confidence_reason = build_confidence_reason(matched_keywords, confidence, intent)
        logger.info(
            "Intent detected | intent=%s matched=%d confidence=%s question_preview='%s'",
            intent, matched_keywords, confidence, request.question[:60]
        )

        # Step 2: Short-circuit for out_of_scope — no cache lookup needed
        if intent == "out_of_scope":
            settings = get_settings()
            system_mode = "sheets" if bool(settings.SHEET_ID) and get_cache().size() > 0 else "fallback"
            response = response_service.format_response("out_of_scope", OUT_OF_SCOPE_DATA)
            response.matched_keywords = 0
            response.confidence = "low"
            response.confidence_reason = confidence_reason
            response.intent_reason = intent_reason
            response.system_mode = system_mode
            response.served_from_cache = False
            response.data_source_note = (
                "Using Google Sheets data (live mode)" if system_mode == "sheets"
                else "Using fallback dataset (Sheets not configured)"
            )
            return response

        # Step 3: Retrieve from cache — track whether it was a hit
        cache = get_cache()
        data = cache.get(intent)
        served_from_cache = data is not None

        if served_from_cache:
            logger.debug("Cache HIT for intent: %s", intent)
        else:
            logger.warning("Cache MISS for intent: %s — using fallback", intent)
            data = fallback_service.get_category_data(intent)

        # Step 3: Determine system mode and data source note
        settings = get_settings()
        system_mode = "sheets" if bool(settings.SHEET_ID) and cache.size() > 0 else "fallback"
        data_source_note = (
            "Using Google Sheets data (live mode)"
            if system_mode == "sheets"
            else "Using fallback dataset (Sheets not configured)"
        )

        # Step 4: Format and return response with all metadata
        response = response_service.format_response(intent, data)
        response.matched_keywords = matched_keywords
        response.confidence = confidence
        response.confidence_reason = confidence_reason
        response.intent_reason = intent_reason
        response.system_mode = system_mode
        response.served_from_cache = served_from_cache
        response.data_source_note = data_source_note
        return response

    except Exception as exc:
        logger.error("Error processing question: %s", exc)
        try:
            fallback_data = fallback_service.get_category_data("faq")
            response = response_service.format_response("faq", fallback_data)
            response.matched_keywords = 0
            response.confidence = "low"
            response.confidence_reason = build_confidence_reason(0, "low", "faq")
            response.intent_reason = "No strong keyword match found → defaulted to 'faq'"
            response.system_mode = "fallback"
            response.served_from_cache = False
            response.data_source_note = "Using fallback dataset (Sheets not configured)"
            return response
        except Exception as fatal:
            logger.critical("Fatal error in fallback handler: %s", fatal)
            return QuestionResponse(
                category="faq",
                title="Election Information",
                overview="We encountered an issue. Please try again or contact your local election office.",
                steps=[],
                documents=[],
                tips=["Visit your local election authority website for assistance."],
                next_action="Contact your local election office for help.",
                matched_keywords=0,
                confidence="low",
                confidence_reason=build_confidence_reason(0, "low", "faq"),
                intent_reason="No strong keyword match found → defaulted to 'faq'",
                system_mode="fallback",
                served_from_cache=False,
                data_source_note="Using fallback dataset (Sheets not configured)",
            )


@router.get("/debug/source", response_model=DebugSourceResponse, summary="Debug: content source info")
async def debug_source() -> DebugSourceResponse:
    """
    Return safe observability information about the current content source.

    This endpoint is evaluator/debug-friendly and does NOT expose any secrets,
    credentials, sheet IDs, or tokens. It only reports operational state.
    """
    try:
        cache = get_cache()
        settings = get_settings()
        cache_size = cache.size()
        cache_loaded = cache_size > 0

        # Determine source mode safely
        # We infer from cache size and config — never expose raw credentials
        has_sheet_config = bool(settings.SHEET_ID)
        fallback_active = not has_sheet_config or cache_size == 0

        content_source = "fallback" if fallback_active else "sheets"

        logger.debug(
            "Debug source requested | source=%s cache_loaded=%s cache_size=%d",
            content_source, cache_loaded, cache_size
        )

        return DebugSourceResponse(
            content_source=content_source,
            cache_loaded=cache_loaded,
            fallback_active=fallback_active,
            cache_size=cache_size,
            app_version=settings.APP_VERSION,
            sheets_configured=settings.is_sheets_configured(),
            sheet_name=settings.WORKSHEET_NAME,
            access_mode=settings.ACCESS_MODE,
            demo_sheet_ready=settings.is_sheets_configured(),
        )
    except Exception as exc:
        logger.error("Error in debug/source endpoint: %s", exc)
        return DebugSourceResponse(
            content_source="fallback",
            cache_loaded=False,
            fallback_active=True,
            cache_size=0,
            app_version="1.0.0",
            sheets_configured=False,
            sheet_name="",
            access_mode="auto",
            demo_sheet_ready=False,
        )
