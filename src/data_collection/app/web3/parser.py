import collections
from typing import Any, Dict, List, Optional

from eth_hash.auto import keccak
from web3 import Web3
from web3.contract import Contract

from app.config import ContractConfig
from app.model.abi import ContractABI
from app.model.contract import ContractCategory, PairContractData, TokenContractData


class ContractParser:
    """Parse contract data"""

    def __init__(
        self, web3: Web3, contracts: List[ContractConfig], contract_abi: ContractABI
    ) -> None:
        self.w3 = web3
        self.contract_abi = contract_abi

        # Load contract categories dict (cache)
        # Cache for 'ContractConfig' indexed by address
        self._contracts_config_cache: Dict[str, ContractConfig] = dict()
        for contract in contracts:
            self._contracts_config_cache[contract.address.lower()] = contract

        # Cache for 'Contract' instances indexed by address
        self._contracts_cache: Dict[str, Contract] = dict()

    def get_contract_category(
        self, contract_address: str
    ) -> Optional[ContractCategory]:
        """Get the contract category by contract address

        Returns:
            category: ContractCategory
        """
        if contract_config := self._contracts_config_cache.get(
            contract_address.lower()
        ):
            return contract_config.category
        return None

    def get_contract_events(self, contract_address: str) -> Optional[List[str]]:
        """Get the contract events by contract address

        Returns:
            List[str]: list of event names
        """
        if contract_config := self._contracts_config_cache.get(
            contract_address.lower()
        ):
            return contract_config.events
        return None

    def _get_contract_abi(
        self, contract_category: ContractCategory
    ) -> Optional[List[Dict[str, Any]]]:
        """Return contract ABI depending on the contract category"""
        abi = None
        if contract_category == ContractCategory.ERC20:
            abi = self.contract_abi.erc20
        elif contract_category == ContractCategory.ERC721:
            abi = self.contract_abi.erc721
        elif contract_category == ContractCategory.ERC1155:
            abi = self.contract_abi.erc1155
        elif contract_category == ContractCategory.UNI_SWAP_V2_PAIR:
            abi = self.contract_abi.UniSwapV2Pair
        elif contract_category == ContractCategory.UNI_SWAP_V2_FACTORY:
            abi = self.contract_abi.UniSwapV2Factory
        return abi

    def is_known_contract_address(self, contract_address: str) -> bool:
        """
        Returns:
            `True` if a contract address is in the list of contracts (in the config),
            `False` otherwise

        Note:
            If this method returns `True`, the consumer will handle the current transaction.
        """
        return self.get_contract_category(contract_address) is not None

    def get_contract(
        self, contract_address: str, category: ContractCategory
    ) -> Contract:
        """
        Returns:
            contract: web3 Contract instance for a given contract address
        """
        address_lower = contract_address.lower()

        # Check cache first
        if contract := self._contracts_cache.get(address_lower):
            return contract

        # Get the correct ABI for the given category
        abi = self._get_contract_abi(contract_category=category)

        # Create a w3 contract instance
        contract = self.w3.eth.contract(address=contract_address, abi=abi)

        # Save contract into cache
        self._contracts_cache[address_lower] = contract

        return contract

    async def get_token_contract_data(
        self, contract: Contract, category: ContractCategory
    ) -> Optional[TokenContractData]:
        """Obtain required data for a token contract (ERC20, ERC721, ERC1155) from web3
        and return a TokenContractData instance

        Returns:
            a ContractData instance or `None`
        """
        if category == ContractCategory.ERC20 or category == ContractCategory.ERC721:
            symbol = await contract.functions.symbol().call()
            name = await contract.functions.name().call()
            decimals = await contract.functions.decimals().call()
            total_supply = await contract.functions.totalSupply().call()
        elif category == ContractCategory.ERC1155:
            # ERC1155 doesn't have any values
            symbol, name, decimals, total_supply = None, None, None, None
        else:
            # Return None if the contract has some other category
            return None

        return TokenContractData(
            address=contract.address,
            symbol=symbol,
            name=name,
            decimals=decimals,
            total_supply=total_supply,
            token_category=category.value,
        )

    async def get_pair_contract_data(
        self, contract: Contract, category: ContractCategory
    ) -> Optional[PairContractData]:
        """Obtain required data for a (uniswap) pair contract from web3 and return a PairContractData instance

        Returns:
            a ContractData instance or `None`
        """
        if category == ContractCategory.UNI_SWAP_V2_PAIR:
            token0 = await contract.functions.token0.call()
            token1 = await contract.functions.token1.call()
            reserve0 = await contract.functions.reserve0.call()
            reserve1 = await contract.functions.reserve1.call()
            factory = await contract.functions.factory.call()
        else:
            # Return None if the contract has unknown category
            return None

        return PairContractData(
            address=contract.address,
            token0=token0,
            token1=token1,
            reserve0=reserve0,
            reserve1=reserve1,
            factory=factory,
        )
