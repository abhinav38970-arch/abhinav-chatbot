import re
from datetime import datetime
from typing import Optional, Tuple
import calendar

class SchoolYearDetector:
    """
    Detects current school year and analyzes content recency
    """
    
    def __init__(self):
        # School year typically runs August-July
        # August 2026 - July 2027 = 2026-2027 school year
        self.current_year = self._detect_current_school_year()
        self.current_month = datetime.now().month
        
    def _detect_current_school_year(self) -> Tuple[int, int]:
        """
        Determine current school year based on month
        School year starts in August
        """
        now = datetime.now()
        year = now.year
        month = now.month
        
        # If we're in January-July, school year is current_year - (current_year + 1)
        # If we're in August-December, school year is current_year - (current_year + 1)
        if month >= 8:  # August-December
            return (year, year + 1)
        else:  # January-July
            return (year - 1, year)
    
    def get_current_school_year(self) -> str:
        """Return current school year as string (e.g., '2026-2027')"""
        return f"{self.current_year[0]}-{self.current_year[1]}"
    
    def get_previous_school_year(self) -> str:
        """Return previous school year"""
        prev_year = (self.current_year[0] - 1, self.current_year[1] - 1)
        return f"{prev_year[0]}-{prev_year[1]}"
    
    def extract_years_from_text(self, text: str) -> list:
        """
        Extract all school year patterns from text
        Looks for patterns like '2026-2027', '2026-27', '2026/27', etc.
        """
        if not text:
            return []
            
        # Patterns for school years
        patterns = [
            r'\b(\d{4})[-/](\d{2,4})\b',  # 2026-2027 or 2026/27 or 2026-27
            r'\b(\d{4})[\s-]?to[\s-]?(\d{4})\b',  # 2026 to 2027
            r'\b(\d{4})[\s-]?through[\s-]?(\d{4})\b',  # 2026 through 2027
            r'\b(\d{4})[\s-]?-\s*(\d{4})\b',  # 2026 - 2027
        ]
        
        years_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                year1 = match[0]
                year2 = match[1]
                if len(year2) == 2:
                    year2 = year1[:2] + year2  # Convert '27' to '2027'
                
                # Validate that year2 is year1 + 1 (school years are consecutive)
                if int(year2) == int(year1) + 1:
                    years_found.append(f"{year1}-{year2}")
        
        return list(set(years_found))  # Remove duplicates
    
    def is_current_school_year_content(self, text: str) -> bool:
        """
        Check if text contains references to current school year
        """
        current_year_str = self.get_current_school_year()
        years_in_text = self.extract_years_from_text(text)
        
        return current_year_str in years_in_text
    
    def get_recency_score(self, text: str, url: str) -> float:
        """
        Calculate a recency score (0-1) where 1 = most current
        Considers:
        - Presence of current school year
        - Absence of old school years  
        - URL patterns suggesting current info
        """
        score = 0.5  # Default neutral score
        
        current_year = self.get_current_school_year()
        previous_year = self.get_previous_school_year()
        
        years_in_text = self.extract_years_from_text(text)
        
        # Boost for current school year
        if current_year in years_in_text:
            score += 0.3
        
        # Penalty for old school years
        if previous_year in years_in_text:
            score -= 0.2
            
        # Check for very old years (2+ years ago)
        old_years = [y for y in years_in_text if y != current_year and y != previous_year]
        if old_years:
            score -= 0.1 * len(old_years)
        
        # URL patterns that suggest current info
        current_patterns = ['current', 'latest', 'update', 'news', str(datetime.now().year)]
        if any(pattern.lower() in url.lower() for pattern in current_patterns):
            score += 0.1
            
        # URL patterns that suggest archives
        archive_patterns = ['archive', 'old', 'past', '2023', '2024']
        if any(pattern.lower() in url.lower() for pattern in archive_patterns):
            score -= 0.2
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def get_content_freshness(self, text: str) -> dict:
        """
        Analyze content freshness and return detailed metadata
        """
        current_year = self.get_current_school_year()
        years_found = self.extract_years_from_text(text)
        
        return {
            'current_school_year': current_year,
            'years_mentioned': years_found,
            'is_current_year': current_year in years_found,
            'recency_score': self.get_recency_score(text, ""),
            'has_outdated_info': any(y != current_year for y in years_found)
        }