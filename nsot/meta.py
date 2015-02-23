"""
Provide a ScopedSession object that is only imported as needed in
certain scopes (such as with classmethods).
"""

from sqlalchemy.orm import scoped_session
from .models import Session

ScopedSession = scoped_session(Session)
