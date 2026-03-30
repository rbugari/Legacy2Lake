from typing import Optional, List, Type
from apps.utm.core.interfaces import CartridgeBase

class CartridgeRegistry:
    """
    Central registry for all Tech-Agnostic V5 Discovery Cartridges.
    """
    
    _registry: List[Type[CartridgeBase]] = []

    @classmethod
    def register(cls, cartridge_class: Type[CartridgeBase]):
        if cartridge_class not in cls._registry:
            cls._registry.append(cartridge_class)

    @classmethod
    def get_cartridge(cls, ext: str, content_hint: str = None) -> Optional[CartridgeBase]:
        """Finds the first cartridge that claims it can handle this file."""
        for cartridge_class in cls._registry:
            instance = cartridge_class()
            if instance.can_handle(ext, content_hint):
                return instance
        return None

# --- Pre-register built-in cartridges ---
from apps.utm.cartridges.ssis.parser import SSISCartridge
CartridgeRegistry.register(SSISCartridge)
