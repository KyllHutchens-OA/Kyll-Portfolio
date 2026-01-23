"""
AFL Analytics Agent - Entity Resolver

Handles team name normalization, nickname mapping, fuzzy matching, and entity validation.
Converts natural language variations to canonical database values.
"""
from typing import Optional, Dict, List, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class EntityResolver:
    """
    Resolves natural language entity references to canonical database values.

    Handles:
    - Team nicknames ("Cats" → "Geelong")
    - Abbreviations ("RIC" → "Richmond")
    - Typos ("Richmnd" → "Richmond")
    - Multiple representations ("Port Adelaide Power" → "Port Adelaide")
    - Case insensitivity
    """

    # Comprehensive team nickname mapping
    # Format: "CanonicalName": [list of all possible variations]
    TEAM_NICKNAMES = {
        "Adelaide": [
            "adelaide", "crows", "adelaide crows", "the crows", "ade"
        ],
        "Brisbane Lions": [
            "brisbane", "brisbane lions", "lions", "the lions", "bri", "brisbane bears"
        ],
        "Carlton": [
            "carlton", "blues", "the blues", "car", "navy blues"
        ],
        "Collingwood": [
            "collingwood", "magpies", "the magpies", "pies", "col", "the pies"
        ],
        "Essendon": [
            "essendon", "bombers", "the bombers", "dons", "ess", "the dons"
        ],
        "Fremantle": [
            "fremantle", "dockers", "the dockers", "freo", "fre"
        ],
        "Geelong": [
            "geelong", "cats", "geelong cats", "the cats", "gee"
        ],
        "Gold Coast": [
            "gold coast", "suns", "gold coast suns", "the suns", "gcs"
        ],
        "Greater Western Sydney": [
            "greater western sydney", "gws", "giants", "gws giants",
            "the giants", "western sydney"
        ],
        "Hawthorn": [
            "hawthorn", "hawks", "the hawks", "haw"
        ],
        "Melbourne": [
            "melbourne", "demons", "the demons", "dees", "mel", "the dees"
        ],
        "North Melbourne": [
            "north melbourne", "kangaroos", "roos", "the roos", "nm",
            "the kangaroos", "north", "shinboners"
        ],
        "Port Adelaide": [
            "port adelaide", "power", "port adelaide power", "the power",
            "pa", "port"
        ],
        "Richmond": [
            "richmond", "tigers", "richmond tigers", "the tigers", "ric", "tiges"
        ],
        "St Kilda": [
            "st kilda", "saints", "the saints", "stk", "st. kilda"
        ],
        "Sydney": [
            "sydney", "swans", "sydney swans", "the swans", "syd", "south melbourne"
        ],
        "West Coast": [
            "west coast", "eagles", "west coast eagles", "the eagles",
            "wce", "weagles"
        ],
        "Western Bulldogs": [
            "western bulldogs", "bulldogs", "dogs", "the dogs", "wb",
            "footscray", "the bulldogs"
        ]
    }

    # Reverse lookup: variation → canonical name
    _NICKNAME_LOOKUP = None

    @classmethod
    def _build_lookup(cls):
        """Build reverse lookup dictionary on first use."""
        if cls._NICKNAME_LOOKUP is None:
            cls._NICKNAME_LOOKUP = {}
            for canonical, variations in cls.TEAM_NICKNAMES.items():
                for variation in variations:
                    cls._NICKNAME_LOOKUP[variation.lower()] = canonical

    @classmethod
    def resolve_team(cls, user_input: str) -> Optional[str]:
        """
        Resolve a team name from user input to canonical database name.

        Tries in order:
        1. Exact match (case-insensitive)
        2. Nickname/abbreviation lookup
        3. Fuzzy matching for typos

        Args:
            user_input: Team name as entered by user (e.g., "Cats", "Tigers", "RIC")

        Returns:
            Canonical team name (e.g., "Geelong") or None if no match
        """
        if not user_input:
            return None

        cls._build_lookup()

        # Normalize input
        normalized = user_input.strip().lower()

        # Try exact nickname lookup
        if normalized in cls._NICKNAME_LOOKUP:
            canonical = cls._NICKNAME_LOOKUP[normalized]
            logger.info(f"Resolved '{user_input}' → '{canonical}' (exact match)")
            return canonical

        # Try fuzzy matching for typos
        fuzzy_match = cls._fuzzy_match_team(normalized)
        if fuzzy_match:
            logger.info(f"Resolved '{user_input}' → '{fuzzy_match}' (fuzzy match)")
            return fuzzy_match

        logger.warning(f"Could not resolve team name: '{user_input}'")
        return None

    @classmethod
    def _fuzzy_match_team(cls, user_input: str, threshold: float = 0.75) -> Optional[str]:
        """
        Find closest team name match using fuzzy string matching.

        Args:
            user_input: Normalized user input
            threshold: Minimum similarity ratio (0.0 to 1.0)

        Returns:
            Best matching canonical team name or None
        """
        best_match = None
        best_score = 0.0

        # Check against all variations
        for canonical, variations in cls.TEAM_NICKNAMES.items():
            for variation in variations:
                similarity = SequenceMatcher(None, user_input, variation).ratio()
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = canonical

        return best_match

    @classmethod
    def validate_entities(cls, entities: Dict) -> Dict:
        """
        Validate and normalize extracted entities.

        Args:
            entities: Raw entities from UNDERSTAND node
                     e.g., {"teams": ["Cats", "Tigers"], "seasons": ["2024"]}

        Returns:
            Validation result with corrected entities and warnings
        """
        result = {
            "is_valid": True,
            "corrected_entities": {},
            "warnings": [],
            "suggestions": []
        }

        # Validate and resolve teams
        if "teams" in entities and entities["teams"]:
            corrected_teams = []
            for team_input in entities["teams"]:
                resolved = cls.resolve_team(team_input)
                if resolved:
                    corrected_teams.append(resolved)
                else:
                    result["is_valid"] = False
                    result["warnings"].append(f"Unknown team: '{team_input}'")
                    result["suggestions"].append(
                        f"Did you mean one of these teams? {', '.join(list(cls.TEAM_NICKNAMES.keys())[:5])}"
                    )

            result["corrected_entities"]["teams"] = corrected_teams

        # Validate seasons (basic range check)
        if "seasons" in entities and entities["seasons"]:
            corrected_seasons = []
            for season in entities["seasons"]:
                try:
                    year = int(season)
                    if 1990 <= year <= 2025:
                        corrected_seasons.append(str(year))
                    else:
                        result["warnings"].append(f"Season {year} outside data range (1990-2025)")
                except (ValueError, TypeError):
                    result["warnings"].append(f"Invalid season: '{season}'")

            result["corrected_entities"]["seasons"] = corrected_seasons

        # Pass through other entities unchanged for now
        for key in ["players", "metrics", "rounds"]:
            if key in entities:
                result["corrected_entities"][key] = entities[key]

        return result

    @classmethod
    def suggest_teams(cls, partial_input: str, limit: int = 5) -> List[str]:
        """
        Suggest team names based on partial input.

        Args:
            partial_input: Partial team name
            limit: Maximum suggestions to return

        Returns:
            List of suggested canonical team names
        """
        if not partial_input:
            return []

        cls._build_lookup()
        normalized = partial_input.strip().lower()

        suggestions = []
        for canonical, variations in cls.TEAM_NICKNAMES.items():
            # Check if any variation starts with the input
            if any(v.startswith(normalized) for v in variations):
                suggestions.append(canonical)
            elif normalized in canonical.lower():
                suggestions.append(canonical)

        return suggestions[:limit]

    @classmethod
    def get_all_canonical_teams(cls) -> List[str]:
        """Get list of all canonical team names."""
        return list(cls.TEAM_NICKNAMES.keys())

    @classmethod
    def get_team_variations(cls, canonical_name: str) -> List[str]:
        """Get all variations/nicknames for a canonical team name."""
        return cls.TEAM_NICKNAMES.get(canonical_name, [])


# Metric normalization
class MetricResolver:
    """Resolves metric aliases to canonical metric names."""

    METRIC_ALIASES = {
        "wins": ["wins", "victories", "won", "win", "w"],
        "losses": ["losses", "defeats", "lost", "loss", "l"],
        "draws": ["draws", "ties", "drawn", "draw", "d"],
        "goals": ["goals", "goals scored", "total goals", "score"],
        "points": ["points", "total points", "score"],
        "margin": ["margin", "winning margin", "margin of victory", "diff", "difference"],
        "percentage": ["percentage", "pct", "%", "win percentage"],
        "ladder_position": ["ladder position", "position", "rank", "ranking", "place"],
    }

    @classmethod
    def resolve_metric(cls, user_input: str) -> Optional[str]:
        """Resolve metric name from user input to canonical name."""
        if not user_input:
            return None

        normalized = user_input.strip().lower()

        for canonical, aliases in cls.METRIC_ALIASES.items():
            if normalized in aliases:
                return canonical

        return None
