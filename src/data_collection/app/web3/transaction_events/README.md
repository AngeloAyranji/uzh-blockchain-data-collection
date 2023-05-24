# Flow of event extraction

1. Get transactions from block.
2. Get receipt from transaction.
3. Get contract from receipt.
4. Read the category from the contract, then decide which ABI to use.
5. Get ABI from contract address from [contact_abi.json](../../../etc/contract_abi.json).
6. When we have the ABI, we know the names of events in the receipt. Map each event to our event representation according 
to **Event mapping**.

# Event mapping
We use [decorator](decorator.py) to associate individual event mappers to the corresponding contract categories. With 
event mappers [erc20.py](erc20.py), [uniswap_pair.py](uniswap_pair.py]), [uniswapv2_factory.py](uniswapv2_factory.py),
we map the retrieved events to appropriate canonical events, which are used in [consumer.py](../../consumer.py) to compute supply change.


# Event representation
We extract the following events from tracked contracts. Events are defined in [types.py](types.py).


## Generic ERC20 contracts
Most ERC20 represent Minting, Burning and Transfering with the Transfer event.
They do so by using transfers from or to account 0.

### TransferFungibleEvent 
````
TransferFungibleEvent(from, to, amount)
````
https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol#L245

Represents a transfer from account `from` to account `to` of `amount` units.

### BurnFungibleEvent
````
BurnFungibleEvent(account, address(0), value)
````

https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol#L298

Represents a transfer from account `account` to burn addresses `address(0)` of `amount` units.

    burn_addresses = {'0x0000000000000000000000000000000000000000',
                     '0x000000000000000000000000000000000000dead'}

### MintFungibleEvent
````
MintFungibleEvent(address(0), account, amount)
````
https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol#L269

Represents a transfer of a minted unit from zero address `account(0)` to an account `account` of `amount` units.

## USDT
USDT uses custom events Issue and Redeem to represent Minting and Burning.
They transfer funds to a programmable address in the contract [owner](https://etherscan.io/address/0xdac17f958d2ee523a2206206994597c13d831ec7#code#L275)
so the recipient of the minted coins might change over time. Events for USDT are mapped to our canonical ERC20 events.

## UniswapV2
UniswapV2 has two types of contracts, a core and a periphery. Periphery contracts allow the traders to add extra 
functionality and they call the core contract (UniswapV2Pair.sol), which emits the events. Hence, we extract the events 
only from the core contract. https://ethereum.org/en/developers/tutorials/uniswap-v2-annotated-code/#contract-types

### Uniswap PairCreatedEvent
````
PairCreatedEvent(token0, token1, pair)
````
https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol#L13

Represents a pair creation in UniswapV2Factory with the token address `token0` and token address `token1` and the 
pair address. 

### Uniswap MintPairEvent
````
MintPairEvent(sender, amount0, amount1)
````
https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L49

Represents creating a pool(liquidty) tokens from a sender address `sender` with amount `amount0` of token0 and amount
`amount1` of token1.

### Uniswap BurnPairEvent
````
BurnPairEvent(sender, amount0, amount1, to)
````
https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L50

Represents destroying the pool tokens. Basically, address of sender `sender` is taking amount of liquidity `amount0` 
of token0 and `amount1` of token1 from the pool to their provided address `to`, which does not have to be equal to `sender`.

### Uniswap SwapPairEvent
````
SwapPairEvent(sender, amount0In, amount1In, amount0Out, amount1Out, to)
````
https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L51

Represents swapping tokens. Address of the trader `sender` swap the tokens. `amount0In`, `amount1In` describe how much 
was sold, and `amount0Out`, `amount1Out` describe how much was received in the token swap by the beneficiary account `to`. 
It doesn't have to be the trader him/herself.  
