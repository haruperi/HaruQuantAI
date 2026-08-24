import asyncio
import json
from typing import Literal

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# 1. Configure the Async Client pointing to your local OAuth proxy
API_OPENAI_URL = "http://127.0.0.1:8317/v1"
API_GEMINI_URL = "http://127.0.0.1:8317"
API_KEY = "123456"

client = AsyncOpenAI(
    base_url=API_OPENAI_URL,
    api_key=API_KEY,
    http_client=httpx.AsyncClient(timeout=15.0),
)


# 2. Define strict structured output schemas for your execution engine
class TradeSignal(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"] = Field(
        description="Trading action recommendation"
    )
    symbol: str = Field(description="Trading symbol, e.g. XAUUSD")
    confidence: float = Field(description="Model confidence level between 0.0 and 1.0")
    entry_price: float | None = Field(None, description="Target entry price level")
    stop_loss: float | None = Field(None, description="Calculated stop loss price")
    take_profit: float | None = Field(None, description="Calculated take profit price")
    reasoning: str = Field(description="Brief rationale for the signal")


# 3. Market Analysis Function
async def analyze_market(market_payload: dict) -> TradeSignal:
    """Sends tick/candle data to the local AI proxy and parses the trade signal."""
    system_prompt = (
        "You are an expert algorithmic trading analyst specializing in gold (XAUUSD) "
        "and multi-timeframe price action. Analyze market conditions and risk-to-reward "
        "profiles."
    )

    response = await client.beta.chat.completions.parse(
        model="gpt-5.6-sol",  # Or 'gpt-5.6', 'gemini-3.1-pro'
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Current Market Snapshot:\n{json.dumps(market_payload, indent=2)}",
            },
        ],
        response_format=TradeSignal,
        temperature=0.2,
        extra_body={"reasoning_effort": "low"},  # 'low', 'medium', or 'high'
    )

    return response.choices[0].message.parsed


# 4. Example Event Loop Integration
async def main():
    sample_market_data = {
        "symbol": "XAUUSD",
        "current_price": 2364.50,
        "timeframe": "M5",
        "atr_14": 3.80,
        "ema_20": 2362.10,
        "ema_50": 2358.40,
        "rsi_14": 62.4,
        "market_structure": "Bullish breakout above prior session high (2360.00)",
    }

    signal = await analyze_market(sample_market_data)

    print(f"Action: {signal.action} {signal.symbol}")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"SL / TP: {signal.stop_loss} / {signal.take_profit}")
    print(f"Reasoning: {signal.reasoning}")


if __name__ == "__main__":
    asyncio.run(main())
