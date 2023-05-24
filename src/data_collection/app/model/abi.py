from typing import Any, Dict, List

from pydantic import BaseModel


class ContractABI(BaseModel):
    """Model for Contract ABIs. The data is loaded from `abi.json`"""

    erc20: List[Dict[str, Any]]
    erc721: List[Dict[str, Any]]
    erc1155: List[Dict[str, Any]]
    UniSwapV2Factory: List[Dict[str, Any]]
    UniSwapV2Pair: List[Dict[str, Any]]
