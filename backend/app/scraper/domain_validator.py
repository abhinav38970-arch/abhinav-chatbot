import re
from urllib.parse import urlparse
from typing import Tuple, Dict
import logging

logger = logging.getLogger("domain_validator")

class DomainValidator:
    """Strict FUSD domain validation with comprehensive checks"""

    FUSD_DOMAIN = "fremontunified.org"

    def __init__(self):
        self.stats = {
            'total_checks': 0,
            'valid_fusd': 0,
            'blocked_external': 0,
            'blocked_paths': 0,
            'blocked_extensions': 0
        }

    def validate_url(self, url: str) -> Tuple[bool, Dict]:
        """
        Validate URL against FUSD domain rules
        Returns: (is_valid, validation_details)
        """
        self.stats['total_checks'] += 1
        result = {
            'url': url,
            'valid': False,
            'reason': '',
            'domain': '',
            'path': '',
            'extension': ''
        }

        try:
            parsed = urlparse(url)
            result['domain'] = parsed.netloc
            result['path'] = parsed.path
            result['extension'] = url.split('.')[-1] if '.' in url else 'none'

            # Check 1: Domain must be exactly FUSD
            if parsed.netloc != self.FUSD_DOMAIN:
                result['reason'] = f"External domain: {parsed.netloc}"
                self.stats['blocked_external'] += 1
                logger.warning(f"🚫 EXTERNAL DOMAIN: {url}")
                return False, result

            # Check 2: Path must be allowed
            path_parts = [p for p in parsed.path.strip("/").split("/") if p]
            if path_parts and not self._is_allowed_path(path_parts):
                result['reason'] = f"Blocked path: {parsed.path}"
                self.stats['blocked_paths'] += 1
                logger.warning(f"🚫 BLOCKED PATH: {url}")
                return False, result

            # Check 3: File extension must be allowed
            if not self._is_allowed_extension(url):
                result['reason'] = f"Blocked extension: {result['extension']}"
                self.stats['blocked_extensions'] += 1
                logger.warning(f"🚫 BLOCKED EXTENSION: {url}")
                return False, result

            result['valid'] = True
            result['reason'] = "Valid FUSD URL"
            self.stats['valid_fusd'] += 1
            logger.info(f"✅ VALID FUSD URL: {url}")
            return True, result

        except Exception as e:
            result['reason'] = f"URL parsing error: {str(e)}"
            logger.error(f"🚨 URL PARSE ERROR: {url} - {str(e)}")
            return False, result

    def _is_allowed_path(self, path_parts: list) -> bool:
        """Check if path is in allowed FUSD paths"""
        from backend.app.config import SCHOOL_CONFIG

        if not path_parts:
            return True  # Root path

        first_part = path_parts[0].lower()

        # Check schools
        school_ids = [s['school_id'] for s in SCHOOL_CONFIG.schools]
        if first_part in school_ids:
            return True

        # Check district sections
        allowed_paths = SCHOOL_CONFIG.get_allowed_paths()
        if (first_part in allowed_paths['district'] or
            first_part in allowed_paths['admin']):
            return True

        # Check blocked paths - use exact match instead of startswith
        blocked_paths = SCHOOL_CONFIG.crawl_rules['domain_isolation']['blocked_paths']
        if first_part in blocked_paths:
            return False
        
        # Allow common legitimate paths that might contain blocked terms
        common_allowed = ['departments', 'services', 'calendar', 'staff', 'contact', 'forms', 'surveys']
        if first_part in common_allowed:
            return True
        
        # Default to False for unknown paths
        return False

    def _is_allowed_extension(self, url: str) -> bool:
        """Check file extension against allowed types"""
        from backend.app.config import SCHOOL_CONFIG

        allowed = SCHOOL_CONFIG.crawl_rules['domain_isolation']['file_extensions']['allow']
        blocked = SCHOOL_CONFIG.crawl_rules['domain_isolation']['file_extensions']['block']

        for ext in blocked:
            if url.lower().endswith(ext):
                return False

        return True

    def get_stats(self) -> Dict:
        """Get validation statistics"""
        return self.stats

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'total_checks': 0,
            'valid_fusd': 0,
            'blocked_external': 0,
            'blocked_paths': 0,
            'blocked_extensions': 0
        }
