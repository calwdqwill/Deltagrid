"""Referral service — Phase 2 placeholder.

Generates referral codes and tracks conversions.
Reward processing deferred to Phase 2+ implementation.
"""

import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import Referral


class ReferralService:
    def __init__(self, db: Session):
        self.db = db

    def generate_code(self, user_id: str) -> str:
        code = secrets.token_urlsafe(8)
        referral = Referral(
            referrer_id=user_id,
            code=code,
            status="pending",
        )
        self.db.add(referral)
        self.db.commit()
        return code

    def get_referral_stats(self, user_id: str) -> dict:
        total = self.db.query(Referral).filter(Referral.referrer_id == user_id).count()
        converted = self.db.query(Referral).filter(
            Referral.referrer_id == user_id,
            Referral.status == "converted",
        ).count()
        return {
            "total_referrals": total,
            "converted": converted,
            "conversion_rate": (converted / total * 100) if total > 0 else 0,
        }
