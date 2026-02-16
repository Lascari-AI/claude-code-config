"""Expertise model for Agent Expert learning."""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Expertise(Base):
    """User expertise model - the Agent Expert's 'mental model'."""
    __tablename__ = "expertise"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    total_improvements: Mapped[int] = mapped_column(Integer, default=0)
    last_improvement_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    expertise_data: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="expertise")

    def get_default_expertise(self) -> dict:
        """Return default expertise structure."""
        return {
            "viewed_products": [],
            "added_to_cart": [],
            "checked_out": []
        }
