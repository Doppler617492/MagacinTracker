"""
UoM (Unit of Measure) and Case-Pack Conversion Service
Ensures consistent quantity handling: BOX ↔ PCS
"""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.logging import get_logger

from ..models.article import Artikal

logger = get_logger(__name__)


class UoMConversionService:
    """
    Handles unit of measure conversions
    
    Rules:
    - All quantities stored in base_uom (typically PCS)
    - Imports in pack_uom (BOX) converted to base_uom
    - Display can show pack equivalent but calculations use base
    - KPI and exports always in base_uom
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_article(self, article_id: UUID) -> Optional[Artikal]:
        """Get article with UoM info"""
        stmt = select(Artikal).where(Artikal.id == article_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def convert_to_base_uom(
        self,
        quantity: Decimal,
        uom: str,
        article: Artikal
    ) -> Decimal:
        """
        Convert quantity from any UoM to base UoM
        
        Examples:
            24 BOX with conversion_factor=12 → 288 PCS
            100 PCS (already base) → 100 PCS
        
        Args:
            quantity: Input quantity
            uom: Unit of measure (PCS, BOX, CASE, etc.)
            article: Article with conversion info
            
        Returns:
            Quantity in base_uom (PCS)
            
        Raises:
            ValueError: If UoM unknown or conversion not possible
        """
        # Already in base UoM
        if uom == article.base_uom:
            return quantity
        
        # Convert from pack UoM to base UoM
        if uom == article.pack_uom:
            if not article.conversion_factor or article.conversion_factor <= 0:
                raise ValueError(
                    f"Cannot convert {uom} to {article.base_uom}: "
                    f"conversion_factor not set for article {article.sifra}"
                )
            
            # BOX * 12 = PCS
            result = quantity * article.conversion_factor
            
            logger.info(
                "uom.convert_to_base",
                article_sifra=article.sifra,
                from_uom=uom,
                to_uom=article.base_uom,
                quantity_in=float(quantity),
                quantity_out=float(result),
                factor=float(article.conversion_factor)
            )
            
            return result
        
        # Unknown UoM
        raise ValueError(
            f"Unknown UoM '{uom}' for article {article.sifra}. "
            f"Expected {article.base_uom} or {article.pack_uom}"
        )
    
    async def convert_from_base_uom(
        self,
        quantity: Decimal,
        target_uom: str,
        article: Artikal
    ) -> Decimal:
        """
        Convert quantity from base UoM to target UoM
        
        Examples:
            288 PCS with conversion_factor=12 → 24 BOX
            100 PCS to PCS → 100 PCS
        
        Args:
            quantity: Quantity in base_uom (PCS)
            target_uom: Target UoM (BOX, CASE, etc.)
            article: Article with conversion info
            
        Returns:
            Quantity in target UoM
        """
        # Already in target UoM
        if target_uom == article.base_uom:
            return quantity
        
        # Convert from base to pack
        if target_uom == article.pack_uom:
            if not article.conversion_factor or article.conversion_factor <= 0:
                raise ValueError(
                    f"Cannot convert to {target_uom}: conversion_factor not set"
                )
            
            # PCS / 12 = BOX
            result = quantity / article.conversion_factor
            
            logger.info(
                "uom.convert_from_base",
                article_sifra=article.sifra,
                from_uom=article.base_uom,
                to_uom=target_uom,
                quantity_in=float(quantity),
                quantity_out=float(result),
                factor=float(article.conversion_factor)
            )
            
            return result
        
        # Unknown target UoM
        raise ValueError(f"Unknown target UoM '{target_uom}'")
    
    async def convert_quantity(
        self,
        quantity: Decimal,
        from_uom: str,
        to_uom: str,
        article_id: UUID
    ) -> Decimal:
        """
        Convert quantity between any two UoMs
        
        Args:
            quantity: Input quantity
            from_uom: Source UoM
            to_uom: Target UoM
            article_id: Article ID
            
        Returns:
            Converted quantity
        """
        article = await self.get_article(article_id)
        if not article:
            raise ValueError(f"Article {article_id} not found")
        
        # Convert to base first, then to target
        base_quantity = await self.convert_to_base_uom(quantity, from_uom, article)
        result = await self.convert_from_base_uom(base_quantity, to_uom, article)
        
        return result
    
    def format_quantity_display(
        self,
        quantity: Decimal,
        article: Artikal,
        show_pack: bool = False
    ) -> str:
        """
        Format quantity for display
        
        Examples:
            288 PCS → "288 PCS" (show_pack=False)
            288 PCS → "288 PCS (24 BOX)" (show_pack=True, factor=12)
        
        Args:
            quantity: Quantity in base_uom
            article: Article with UoM info
            show_pack: Whether to show pack equivalent
            
        Returns:
            Formatted string (Serbian)
        """
        base_display = f"{quantity:.3f} {article.base_uom}".rstrip('0').rstrip('.')
        
        if show_pack and article.pack_uom and article.conversion_factor:
            pack_quantity = quantity / article.conversion_factor
            pack_display = f"{pack_quantity:.2f} {article.pack_uom}".rstrip('0').rstrip('.')
            return f"{base_display} ({pack_display})"
        
        return base_display

