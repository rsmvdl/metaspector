# metaspector/matrices/rating_matrix.py
# !/usr/bin/env python3

from typing import List, Tuple, Optional

def get_ratings_matrix() -> List[Tuple[str, str, int]]:
    """Returns the comprehensive ratings matrices."""
    ratings_matrix_references = [
        # Australia Ratings
        ('au-movie', 'E', 0),
        ('au-movie', 'G', 0),
        ('au-movie', 'PG', 8),
        ('au-movie', 'M', 15),
        ('au-movie', 'MA 15+', 15),
        ('au-movie', 'R18+', 18),
        ('au-movie', 'X18+', 18),
        ('au-movie', 'UNRATED', 18),
        ('au-tv', 'P', 0),
        ('au-tv', 'C', 8),
        ('au-tv', 'G', 13),
        ('au-tv', 'PG', 8),
        ('au-tv', 'M', 15),
        ('au-tv', 'MA 15+', 15),
        ('au-tv', 'AV 15+', 15),
        ('au-tv', 'UNRATED', 18),

        # Canada Ratings
        ('ca-movie', 'G', 0),
        ('ca-movie', 'PG', 8),
        ('ca-movie', '14', 14),
        ('ca-movie', '14A', 14),
        ('ca-movie', '18', 18),
        ('ca-movie', '18A', 18),
        ('ca-movie', 'R', 18),
        ('ca-movie', 'E', 18),
        ('ca-movie', 'UNRATED', 18),
        ('ca-tv', 'C', 0),
        ('ca-tv', 'C8', 8),
        ('ca-tv', 'G', 13),
        ('ca-tv', 'PG', 18),
        ('ca-tv', '14+', 14),
        ('ca-tv', '18+', 18),
        ('ca-tv', 'UNRATED', 18),

        # Germany Ratings
        ('de-movie', 'ab 0 Jahren', 0),
        ('de-movie', 'ab 6 Jahren', 6),
        ('de-movie', 'ab 12 Jahren', 12),
        ('de-movie', 'ab 16 Jahren', 16),
        ('de-movie', 'ab 18 Jahren', 18),

        # Spain Ratings
        ('es-movie', 'ICAA A / TP', 0),
        ('es-movie', 'ICAA 7', 7),
        ('es-movie', 'ICAA 12', 12),
        ('es-movie', 'ICAA 16', 16),
        ('es-movie', 'ICAA 18', 18),
        ('es-movie', 'ICAA SC', 18),

        # France Ratings
        ('fr-movie', 'U', 0),
        ('fr-movie', '10', 10),
        ('fr-movie', '12', 12),
        ('fr-movie', '16', 16),
        ('fr-movie', '18', 18),
        ('fr-movie', 'E', 18),
        ('fr-tv', '10', 10),
        ('fr-tv', '12', 12),
        ('fr-tv', '16', 16),
        ('fr-tv', '18', 18),

        # Ireland Ratings
        ('ie-movie', 'G', 0),
        ('ie-movie', 'PG', 8),
        ('ie-movie', '12', 12),
        ('ie-movie', '15', 15),
        ('ie-movie', '16', 16),
        ('ie-movie', '18', 18),
        ('ie-movie', 'UNRATED', 18),
        ('ie-tv', 'GA', 0),
        ('ie-tv', 'Ch', 8),
        ('ie-tv', 'YA', 18),
        ('ie-tv', 'PS', 18),
        ('ie-tv', 'MA', 18),
        ('ie-tv', 'UNRATED', 18),

        # Italy Ratings
        ('it-movie', 'T', 0),
        ('it-movie', 'VM14', 14),
        ('it-movie', 'VM18', 18),

        # Japan Ratings
        ('jp-movie', 'G', 0),
        ('jp-movie', 'PG12', 12),
        ('jp-movie', 'R15+', 15),
        ('jp-movie', 'R18+', 18),

        # New Zealand Ratings
        ('nz-movie', 'E', 0),
        ('nz-movie', 'G', 0),
        ('nz-movie', 'PG', 8),
        ('nz-movie', 'M', 13),
        ('nz-movie', 'R13', 13),
        ('nz-movie', 'R15', 15),
        ('nz-movie', 'R16', 16),
        ('nz-movie', 'R18', 18),
        ('nz-movie', 'R', 18),
        ('nz-movie', 'UNRATED', 18),
        ('nz-tv', 'G', 8),
        ('nz-tv', 'PGR', 18),
        ('nz-tv', 'AO', 18),
        ('nz-tv', 'UNRATED', 18),

        # United Kingdom Ratings
        ('uk-movie', 'U', 0),
        ('uk-movie', 'Uc', 0),
        ('uk-movie', 'PG', 8),
        ('uk-movie', '12', 12),
        ('uk-movie', '12A', 12),
        ('uk-movie', '15', 15),
        ('uk-movie', '18', 18),
        ('uk-movie', 'R18', 18),
        ('uk-tv', 'Caution', 15),
        ('uk-movie', 'E', 18),
        ('uk-movie', 'UNRATED', 18),

        # United States Ratings
        ('mpaa', 'G', 0),
        ('mpaa', 'PG', 8),
        ('mpaa', 'PG-13', 13),
        ('mpaa', 'R', 17),
        ('mpaa', 'NC-17', 17),
        ('mpaa', 'UNRATED', 18),
        ('mpaa', 'NOT RATED', 18),
        ('us-tv', 'TV-Y', 0),
        ('us-tv', 'TV-Y7', 7),
        ('us-tv', 'TV-G', 0),
        ('us-tv', 'TV-PG', 10),
        ('us-tv', 'TV-14', 14),
        ('us-tv', 'TV-MA', 17),
    ]
    return ratings_matrix_references

# Create a mapping for efficient lookups
_ratings_map = {
    (system, label): age
    for system, label, age in get_ratings_matrix()
}

def get_age_classification(system: str, label: str) -> Optional[int]:
    """
    Looks up the age classification from a rating system and label.
    """
    if not system or not label:
        return None
    return _ratings_map.get((system, label))
