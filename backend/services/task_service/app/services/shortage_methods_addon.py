"""
Add these methods to ShortageService class in shortage.py
"""

async def complete_partial(
    self,
    stavka_id: UUID,
    request: PartialCompleteRequest,
    user_id: UUID,
) -> PartialCompleteResponse:
    """
    Complete a task with partial quantity (Manhattan-style).
    Wrapper method that delegates to shortage_partial module.
    """
    return await _complete_partial(self.session, stavka_id, request, user_id)


async def markiraj_preostalo(
    self,
    stavka_id: UUID,
    request: MarkirajPreostaloRequest,
    user_id: UUID,
):
    """
    Mark remaining quantity as 0 (Serbian: Markiraj preostalo = 0).
    Wrapper method that delegates to shortage_partial module.
    """
    return await _markiraj_preostalo(self.session, stavka_id, request, user_id)

