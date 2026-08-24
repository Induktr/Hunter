from typing import List
from pydantic import BaseModel, Field

class LeadResearchItem(BaseModel):
    """
    TSD-Enhanced Structured model for B2B Lead & Company Research.
    Directly aligns with Excel export and provides deep architectural & outreach intelligence.
    """
    name: str = Field(
        alias="Name",
        description="Name of the company, startup, client, or product"
    )
    location: str = Field(
        alias="Location",
        description="Location, headquarters, or 'Remote'"
    )
    root_and_tech: str = Field(
        alias="Root Concept & Tech",
        description="Фаза 0: Корневой технологический концепт и стек (Root -> Branch -> Leaf)"
    )
    pain_and_friction: str = Field(
        alias="Pain Type & Friction",
        description="Фаза 1 & 3: Диагноз боли ('БОЛЕУТОЛЯЮЩЕЕ' / 'ВИТАМИН') и скрытое трение бизнеса"
    )
    price_value: str = Field(
        alias="Price/Value",
        description="Оценка бюджета, раунда финансирования или стоимости ($5k-$20k, Series A, N/A)"
    )
    spof_diagnosis: str = Field(
        alias="SPOF & Risk Diagnosis",
        description="Фаза 5: Выявленная точка отказа (SPOF) и направление для оптимизации"
    )
    outreach_hook: str = Field(
        alias="Outreach Pitch Hook",
        description="Фаза 6 & 7: Крючок для первого сообщения с No-Oriented вопросом"
    )
    link: str = Field(
        alias="Link",
        description="Прямой URL сайта, профиля LinkedIn или источника"
    )

    class Config:
        populate_by_name = True


class LeadResearchResult(BaseModel):
    """
    TSD-Powered B2B research result wrapper for Gemini structured schema.
    """
    leads: List[LeadResearchItem] = Field(
        default_factory=list,
        description="Top relevant leads and companies thoroughly audited through TSD v27.2.2 methodology"
    )
