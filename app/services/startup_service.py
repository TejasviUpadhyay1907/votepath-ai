"""Startup orchestration service"""

import logging
from typing import Dict, Optional
from app.core.config import Settings, get_settings
from app.core.logging_config import setup_logging
from app.services.sheets_service import SheetsService
from app.services.fallback_service import FallbackService
from app.utils.cache import get_cache

logger = logging.getLogger(__name__)


class StartupService:
    """Service for orchestrating application startup sequence"""
    
    def __init__(self):
        """Initialize startup service"""
        self.config: Optional[Settings] = None
        self.mode: str = "fallback"
        self.sheets_loaded: bool = False
    
    def _load_configuration(self) -> Settings:
        """
        Load and validate configuration
        
        Returns:
            Settings: Application configuration
        """
        config = get_settings()
        
        if not config.validate_config():
            logger.warning("Configuration validation failed, using defaults")
        
        return config
    
    def _initialize_logging(self, config: Settings) -> None:
        """
        Configure logging system
        
        Args:
            config: Application settings
        """
        setup_logging(config.LOG_LEVEL)
        logger.info(f"Logging initialized at {config.LOG_LEVEL} level")
    
    def _attempt_sheets_load(self) -> Optional[Dict]:
        """
        Best-effort attempt to load data from Google Sheets
        
        Returns:
            Optional[Dict]: Loaded data or None if failed
        """
        try:
            logger.info("Attempting to load data from Google Sheets...")
            
            sheets_service = SheetsService(self.config)
            
            # Try to initialize
            if not sheets_service.initialize():
                logger.info("Sheets initialization failed, will use fallback data")
                return None
            
            # Try to load data
            data = sheets_service.load_data()
            
            if not data:
                logger.warning("Sheets load returned empty data, will use fallback")
                return None
            
            logger.info(f"Successfully loaded {len(data)} categories from Google Sheets")
            return data
            
        except Exception as e:
            logger.warning(f"Exception during Sheets load: {e}")
            return None
    
    def _load_fallback_data(self) -> Dict:
        """
        Load bundled fallback data
        
        Returns:
            Dict: Fallback data
        """
        try:
            logger.info("Loading fallback data...")
            fallback_service = FallbackService()
            data = fallback_service.get_fallback_data()
            logger.info(f"Loaded {len(data)} categories from fallback data")
            return data
        except Exception as e:
            logger.error(f"Failed to load fallback data: {e}")
            # Return minimal fallback
            return {
                "faq": {
                    "title": "FAQ",
                    "overview": "Frequently asked questions",
                    "steps": [],
                    "documents": [],
                    "tips": [],
                    "next_action": ""
                }
            }
    
    def _populate_cache(self, data: Dict) -> None:
        """
        Populate cache with loaded data
        
        Args:
            data: Data to cache
        """
        try:
            cache = get_cache()
            cache.populate(data)
            logger.info(f"Cache populated with {cache.size()} entries")
        except Exception as e:
            logger.error(f"Failed to populate cache: {e}")
    
    def initialize_application(self) -> dict:
        """
        Execute complete startup sequence
        
        Returns:
            dict: Startup summary with mode, sheets_loaded, cache_size
        """
        try:
            # Step 1: Load configuration
            self.config = self._load_configuration()
            logger.info(f"Starting {self.config.APP_NAME} v{self.config.APP_VERSION}")
            
            # Step 2: Initialize logging
            self._initialize_logging(self.config)
            
            # Step 3: Attempt to load from Google Sheets (best-effort)
            sheets_data = self._attempt_sheets_load()
            
            # Step 4: Determine data source
            if sheets_data:
                self.mode = "sheets"
                self.sheets_loaded = True
                data = sheets_data
                logger.info("Operating in SHEETS mode")
            else:
                self.mode = "fallback"
                self.sheets_loaded = False
                data = self._load_fallback_data()
                logger.info("Operating in FALLBACK mode")
            
            # Step 5: Populate cache
            self._populate_cache(data)
            
            # Step 6: Return startup summary
            cache = get_cache()
            summary = {
                "mode": self.mode,
                "sheets_loaded": self.sheets_loaded,
                "cache_size": cache.size()
            }
            
            logger.info(f"Startup complete: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Critical error during startup: {e}")
            # Even on critical error, try to start with minimal fallback
            try:
                self.mode = "fallback"
                self.sheets_loaded = False
                data = self._load_fallback_data()
                self._populate_cache(data)
                cache = get_cache()
                return {
                    "mode": "fallback",
                    "sheets_loaded": False,
                    "cache_size": cache.size()
                }
            except Exception as fatal:
                logger.critical(f"Fatal startup error: {fatal}")
                raise


# Global startup service instance
_startup_service: Optional[StartupService] = None


def get_startup_service() -> StartupService:
    """
    Get global startup service instance
    
    Returns:
        StartupService: Startup service instance
    """
    global _startup_service
    if _startup_service is None:
        _startup_service = StartupService()
    return _startup_service
