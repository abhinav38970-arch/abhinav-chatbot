import json
import os
from typing import Dict, List
import logging

logger = logging.getLogger("school_config")

class SchoolConfig:
    def __init__(self):
        self.schools = []
        self.crawl_rules = {}
        self._load_configurations()
        self._validate_config()

    def _load_configurations(self):
        """Load all configuration files"""
        try:
            # Load schools
            schools_path = os.path.join(os.path.dirname(__file__), 'schools.json')
            with open(schools_path, 'r') as f:
                config_data = json.load(f)
                self.schools = config_data['schools']
                if 'district' in config_data:
                    self.district = config_data['district']

            # Load crawl rules
            rules_path = os.path.join(os.path.dirname(__file__), 'crawl_rules.json')
            with open(rules_path, 'r') as f:
                self.crawl_rules = json.load(f)

            logger.info(f"✅ Loaded {len(self.schools)} schools and crawl rules")

        except FileNotFoundError as e:
            logger.error(f"🚨 Config file not found: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"🚨 Invalid JSON in config: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"🚨 Config load error: {str(e)}")
            raise

    def _validate_config(self):
        """Validate configuration integrity"""
        errors = []

        # Validate schools
        required_school_fields = ['school_id', 'school_name', 'school_level', 'base_urls']
        for school in self.schools:
            for field in required_school_fields:
                if field not in school:
                    errors.append(f"School missing {field}: {school.get('school_name', 'unknown')}")

            # Validate URLs
            for url in school['base_urls']:
                if not url.startswith('https://fremontunified.org/'):
                    errors.append(f"Invalid base URL for {school['school_name']}: {url}")

        # Validate domain isolation
        if not self.crawl_rules.get('domain_isolation', {}).get('strict_domain_match'):
            errors.append("Domain isolation must be strict")

        if errors:
            for error in errors:
                logger.error(f"🚨 CONFIG ERROR: {error}")
            raise ValueError(f"Configuration validation failed with {len(errors)} errors")

        logger.info("✅ Configuration validation passed")

    def get_school_by_id(self, school_id: str) -> Dict:
        """Get school configuration by ID"""
        for school in self.schools:
            if school['school_id'] == school_id:
                return school
        raise ValueError(f"School {school_id} not found")

    def get_schools_by_level(self, level: str) -> List[Dict]:
        """Get all schools of a specific level"""
        return [s for s in self.schools if s['school_level'] == level]

    def get_allowed_paths(self) -> Dict:
        """Get all allowed FUSD paths"""
        return self.crawl_rules['domain_isolation']['allowed_paths']

    def get_all_school_ids(self) -> List[str]:
        """Get list of all school IDs"""
        return [s['school_id'] for s in self.schools]

# Singleton instance
SCHOOL_CONFIG = SchoolConfig()
