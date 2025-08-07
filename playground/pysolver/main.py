import datetime
import json
import pprint
from typing import Annotated, Dict, List, Literal, Optional, Union

from fastapi import Body, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from models import *


# --------------------------------------------------------------------------
# 2. FastAPI Application
# --------------------------------------------------------------------------

app = FastAPI(
    title="Solver API",
    description="A mock implementation of the Solver API for Autopilot queries.",
    version="0.0.1",
)

def get_mock_address(index: int = 0) -> Address:
    return f"0x{'1'*(39-len(str(index)))}{index}aBcDeF"

# --- API Endpoints ---

@app.get(
    "/quote",
    response_model=QuoteResponseKind,
    summary="Get price estimation quote",
    tags=["Solver"],
)
async def get_quote(
    sellToken: Address = Query(..., example=get_mock_address(1)),
    buyToken: Address = Query(..., example=get_mock_address(2)),
    kind: Literal["buy", "sell"] = Query(...),
    amount: TokenAmount = Query(..., example="1000000000000000000"),
    deadline: DateTime = Query(...),
):
    """
    Provides a mock price estimation quote.
    
    HOW IT'S CALLED BY THE DRIVER:
    The driver's source code confirms it calls this endpoint via an HTTP GET
    request. The parameters (sellToken, buyToken, etc.) are sent as query
    strings in the URL, not in a request body.
    Ref: /crates/driver/src/infra/api/routes/quote/mod.rs [cite: 881, 882]
    """
    if kind == "sell":
        buy_amount = str(int(amount) * 95 // 100)
        sell_amount = amount
    else: # kind == "buy"
        sell_amount = str(int(amount) * 100 // 95)
        buy_amount = amount

    return QuoteResponse(
        clearingPrices={
            sellToken: "1000000000000000000",
            buyToken: "950000000000000000",
        },
        preInteractions=[],
        interactions=[],
        solver=get_mock_address(0),
        gas=150000,
        txOrigin=None,
        jitOrders=[],
    )

@app.post(
    "/solve",
    response_model=SolveResponse,
    summary="Solve the passed in auction",
    tags=["Solver"],
)
async def solve_auction(request: SolverRequest):
    """
    This endpoint now returns a response body that is fully compliant with the
    structs defined in the `solvers-dto` crate, resolving the client-side
    parsing error.
    """
    first_order = request.orders[0] if request.orders else None
    first_liquidity = request.liquidity[0] if request.liquidity else None

    # We can only build a mock solution if we have an order to fill
    if not first_order or not first_liquidity:
        return SolveResponse(solutions=[])

    # Create a mock solution that conforms to the `solvers-dto` specification
    mock_solution = Solution(
        id=0, # The required 'id' field for the solution 
        prices={
            first_order.sellToken: first_order.buyAmount,
            first_order.buyToken: first_order.sellAmount,
        },
        trades=[
            TradeFulfillment(
                order=first_order.uid,
                executedAmount=first_order.sellAmount,
            )
        ],
        interactions=[
            LiquidityInteraction(
                internalize=False,
                id=first_liquidity.id,
                inputToken=first_order.sellToken,
                outputToken=first_order.buyToken,
                inputAmount=first_order.sellAmount,
                outputAmount=first_order.buyAmount,
            )
        ],
        gas=250000,
    )

    # The top-level response object just contains the list of solutions 
    return SolveResponse(solutions=[mock_solution])

# ##########################################################################

# Other endpoints for completeness
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post(
    "/reveal",
    response_model=RevealResponse,
    summary="Reveal the calldata of the previously solved auction",
    tags=["Solver"],
)
async def reveal_solution(request: RevealRequest):
    """
    Reveals mock calldata for a given solution ID.

    HOW IT'S CALLED BY THE DRIVER:
    The driver calls this endpoint via POST with a simple JSON body
    containing the `solutionId` and `auctionId`.
    Ref: /crates/driver/src/infra/api/routes/reveal/mod.rs [cite: 901, 902]
    """
    return RevealResponse(
        calldata=Calldata(
            internalized="0xdeadbeef1234",
            uninternalized="0xfeedface5678"
        )
    )

@app.post(
    "/settle",
    status_code=200,
    summary="Execute the previously solved auction on chain",
    tags=["Solver"],
)
async def settle_solution(request: SettleRequest):
    """
    Accepts a request to execute a solution.

    HOW IT'S CALLED BY THE DRIVER:
    The driver calls this endpoint via POST with a JSON body containing
    the `solutionId`, `submissionDeadlineLatestBlock` and `auctionId`.
    Ref: /crates/driver/src/infra/api/routes/settle/mod.rs [cite: 914, 915]
    """
    print(f"Accepted request to settle solution {request.solutionId} for auction {request.auctionId}.")
    return {}

@app.post(
    "/notify",
    status_code=200,
    summary="Receive a notification with a specific reason",
    tags=["Solver"],
)
async def receive_notification(
    # The driver sends a more complex notification object than the OpenAPI spec suggests.
    # For simplicity, we accept a raw dictionary and print it.
    notification: Dict
):
    """
    Receives a notification from the driver.

    HOW IT'S CALLED BY THE DRIVER:
    The driver sends various notifications (e.g., Timeout, Banned, Settled)
    to this endpoint via a POST request with a JSON body.
    Ref: /crates/driver/src/infra/solver/dto/notification.rs [cite: 1265, 1266]
    """
    print(f"Notification received: {notification}")
    return {}