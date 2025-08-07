import datetime
from typing import Dict, List, Literal, Optional, Union, Annotated


from pydantic import BaseModel, Field, field_validator
# --- Component Schemas ---

Address = Annotated[str, Field(description="20 byte Ethereum address encoded as a hex with `0x` prefix.", example="0x6810e776880c02933d47db1b9fc05908e5386b96")]
TokenAmount = Annotated[str, Field(description="Amount of an ERC20 token. 256 bit unsigned integer in decimal notation.", example="12345678901234567890")]
BigUint = Annotated[str, Field(description="A big unsigned integer encoded in decimal.", example="98765432109876543210")]
OrderUID = Annotated[str, Field(description="Unique identifier for the order: 56 bytes encoded as hex with `0x` prefix.", example="0x30cff40d9f60caa68a37f0ee73253ad6ad72b45580c945fe3ab67596476937197854163b1b0d24e77dca702b97b5cc33e0f83dcb626122a6")]
DateTime = Annotated[datetime.datetime, Field(description="An ISO 8601 UTC date time string.", example="2025-08-06T15:18:31.814523Z")]


class Interaction(BaseModel):
    target: Address
    value: TokenAmount
    callData: str = Field(..., description="Hex encoded bytes with `0x` prefix.")

class Token(BaseModel):
    address: Address
    price: Optional[TokenAmount] = Field(None, description="The reference price denominated in native token.")
    trusted: bool = Field(..., description="Whether the protocol trusts the token to be used for internalizing trades.")

class Quote(BaseModel):
    sellAmount: TokenAmount
    buyAmount: TokenAmount
    fee: TokenAmount
    solver: Address

# --- FeePolicy Schemas (using a discriminated union) ---

class SurplusFee(BaseModel):
    kind: Literal["surplus"]
    maxVolumeFactor: float = Field(..., example=0.1)
    factor: float = Field(..., example=0.5)

class PriceImprovement(BaseModel):
    kind: Literal["priceImprovement"]
    maxVolumeFactor: float = Field(..., example=0.01)
    factor: float = Field(..., example=0.5)
    quote: Quote

class VolumeFee(BaseModel):
    kind: Literal["volume"]
    factor: float = Field(..., example=0.5)

FeePolicy = Annotated[
    Union[SurplusFee, PriceImprovement, VolumeFee],
    Field(discriminator="kind")
]

class JitOrder(BaseModel):
    sellToken: Address
    buyToken: Address
    sellAmount: TokenAmount
    buyAmount: TokenAmount
    executedAmount: TokenAmount
    receiver: Address
    validTo: int
    side: Literal["buy", "sell"]
    partiallyFillable: bool
    sellTokenSource: Literal["erc20", "internal", "external"]
    buyTokenSource: Literal["erc20", "internal"]
    appData: str
    signature: str = Field(..., description="Hex encoded bytes with `0x` prefix.")
    signingScheme: Literal["eip712", "ethsign", "presign", "eip1271"]

class Order(BaseModel):
    uid: OrderUID
    sellToken: Address
    buyToken: Address
    sellAmount: TokenAmount
    buyAmount: TokenAmount
    created: str = Field(..., example="123456")
    validTo: int
    kind: Literal["buy", "sell"]
    receiver: Address
    owner: Address
    partiallyFillable: bool
    executed: TokenAmount
    preInteractions: List[Interaction]
    postInteractions: List[Interaction]
    sellTokenBalance: Literal["erc20", "internal", "external"]
    buyTokenBalance: Literal["erc20", "internal"]
    klass: Literal["market", "limit"] = Field(..., alias="class")
    appData: str
    signingScheme: Literal["eip712", "ethsign", "presign", "eip1271"]
    signature: str
    protocolFees: List[FeePolicy]
    quote: Optional[Quote] = None

class Calldata(BaseModel):
    internalized: str = Field(..., example="0x1234")
    uninternalized: str = Field(..., example="0x5678")

class Error(BaseModel):
    kind: str
    description: str

# --- Quote Response Schemas ---

class LegacyQuoteResponse(BaseModel):
    amount: TokenAmount
    interactions: List[Interaction]
    solver: Address
    gas: int
    txOrigin: Optional[Address] = None

class QuoteResponse(BaseModel):
    clearingPrices: Dict[Address, BigUint]
    preInteractions: List[Interaction]
    interactions: List[Interaction]
    solver: Address
    gas: int
    txOrigin: Optional[Address] = None
    jitOrders: List[JitOrder]

QuoteResponseKind = Union[QuoteResponse, LegacyQuoteResponse, Error]

# --- Solve Endpoint Schemas ---

class SolveRequest(BaseModel):
    id: int
    orders: List[Order]
    tokens: List[Token]
    deadline: DateTime
    surplusCapturingJitOrderOwners: List[Address]

class SolutionOrderDetail(BaseModel):
    side: Literal["buy", "sell"]
    sellToken: Address
    buyToken: Address
    limitSell: TokenAmount
    limitBuy: TokenAmount
    executedSell: TokenAmount
    executedBuy: TokenAmount




# --- Reveal Endpoint Schemas ---

class RevealRequest(BaseModel):
    solutionId: int = Field(..., example=1)
    auctionId: int = Field(..., example=123)

class RevealResponse(BaseModel):
    calldata: Calldata

# --- Settle Endpoint Schemas ---

class SettleRequest(BaseModel):
    solutionId: int = Field(..., example=1)
    submissionDeadlineLatestBlock: int = Field(..., example=12345)
    auctionId: int = Field(..., example=123)


# --- The main request body model for /solve ---

##### new

# --- Models for the INCOMING /solve request body ---
# (These were corrected in the previous step and remain valid)

class SolverTokenBalance(BaseModel):
    balance: TokenAmount

class SolverLiquidity(BaseModel):
    address: Address
    fee: str
    gasEstimate: TokenAmount
    id: str
    kind: str
    router: Address
    tokens: Dict[Address, SolverTokenBalance]

class SolverTokenInfo(BaseModel):
    availableBalance: TokenAmount
    decimals: Optional[int] = None
    referencePrice: Optional[TokenAmount] = None
    symbol: Optional[str] = None
    trusted: bool

class SolverOrder(BaseModel):
    appData: str
    buyAmount: TokenAmount
    buyToken: Address
    buyTokenDestination: str
    klass: Literal["market", "limit"] = Field(..., alias="class")
    fullBuyAmount: TokenAmount
    fullSellAmount: TokenAmount
    kind: Literal["buy", "sell"]
    owner: Address
    partiallyFillable: bool
    postInteractions: List = []
    preInteractions: List = []
    sellAmount: TokenAmount
    sellToken: Address
    sellTokenSource: str
    signature: str
    signingScheme: str
    uid: OrderUID
    validTo: int
    receiver: Optional[Address] = None
    created: Optional[str] = None
    executed: Optional[TokenAmount] = None
    protocolFees: List = []

class SolverRequest(BaseModel):
    deadline: DateTime
    effectiveGasPrice: TokenAmount
    id: Optional[int] = None
    liquidity: List[SolverLiquidity]
    orders: List[SolverOrder]
    surplusCapturingJitOrderOwners: List[Address]
    tokens: Dict[Address, SolverTokenInfo]

    @field_validator("id", mode="before")
    @classmethod
    def anystr_to_int(cls, v):
        if v is None:
            return v
        return int(v)


# --- Models for the OUTGOING /solve response body ---
# (These are now refactored to match solvers-dto/src/solution.rs)

class TradeFulfillment(BaseModel):
    kind: Literal["fulfillment"] = "fulfillment"
    order: OrderUID
    executedAmount: TokenAmount
    fee: Optional[TokenAmount] = None

class LiquidityInteraction(BaseModel):
    kind: Literal["liquidity"] = "liquidity"
    internalize: bool
    id: str
    inputToken: Address
    outputToken: Address
    inputAmount: TokenAmount
    outputAmount: TokenAmount

class Solution(BaseModel):
    # This field MUST be 'id', not 'solutionId'
    # Ref: /crates/solvers-dto/src/solution.rs 
    id: int
    prices: Dict[Address, TokenAmount]
    trades: List[TradeFulfillment]
    interactions: List[LiquidityInteraction]
    gas: Optional[int] = None

class SolveResponse(BaseModel):
    # The top-level response is just an object with a "solutions" key.
    # Ref: /crates/solvers-dto/src/solution.rs 
    solutions: List[Solution]
