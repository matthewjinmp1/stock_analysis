#!/usr/bin/env python3
"""
Calculate token cost for Grok API usage
"""

# Grok API pricing (per million tokens)
# Reasoning tokens are charged at output rate
GROK_PRICING = {
    "grok-4-1-fast-reasoning": {"input": 0.20, "output": 0.50, "reasoning": 0.50},
    "grok-3-fast": {"input": 5.0, "output": 15.0, "reasoning": 15.0},
    "grok-3": {"input": 3.0, "output": 15.0, "reasoning": 15.0},
}

def calculate_grok_cost(token_usage: dict, model: str = "grok-4-1-fast-reasoning") -> float:
    """Calculate cost in dollars based on token usage including reasoning tokens."""
    pricing = GROK_PRICING.get(model, GROK_PRICING["grok-4-1-fast-reasoning"])

    # Extract token counts
    input_tokens = token_usage.get('prompt_tokens', 0)
    completion_tokens = token_usage.get('completion_tokens', 0)
    total_tokens = token_usage.get('total_tokens', 0)
    thinking_tokens = token_usage.get('thinking_tokens', 0)
    output_tokens = token_usage.get('output_tokens', completion_tokens)

    print(f"Token Usage Breakdown:")
    print(f"  Prompt tokens: {input_tokens:,}")
    print(f"  Completion tokens: {completion_tokens:,}")
    print(f"  Thinking tokens: {thinking_tokens:,}")
    print(f"  Output tokens: {output_tokens:,}")
    print(f"  Total tokens: {total_tokens:,}")
    print()

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    thinking_cost = (thinking_tokens / 1_000_000) * pricing["reasoning"]

    # Convert to cents for display
    input_cost_cents = input_cost * 100
    output_cost_cents = output_cost * 100
    thinking_cost_cents = thinking_cost * 100

    print(f"Cost Calculation ({model}):")
    print(f"  Input cost: {input_cost_cents:.4f} cents ({input_tokens:,} tokens @ ${pricing['input']}/1M)")
    print(f"  Output cost: {output_cost_cents:.4f} cents ({output_tokens:,} tokens @ ${pricing['output']}/1M)")
    print(f"  Thinking cost: {thinking_cost_cents:.4f} cents ({thinking_tokens:,} tokens @ ${pricing['reasoning']}/1M)")

    total_cost = input_cost + output_cost + thinking_cost
    total_cost_cents = total_cost * 100
    print(f"  Total cost: {total_cost_cents:.4f} cents")
    print()

    return total_cost

# Example usage with the provided token data
if __name__ == "__main__":
    # Token usage from user's example
    token_usage = {
        'prompt_tokens': 456,
        'completion_tokens': 2560,
        'total_tokens': 3016,
        'thinking_tokens': 2523,
        'output_tokens': 2560
    }

    print("Grok Token Cost Calculator")
    print("=" * 40)

    cost = calculate_grok_cost(token_usage, "grok-4-1-fast-reasoning")

    cost_cents = cost * 100
    print(".4f")
    print()
    print("Note: Thinking tokens are charged at the same rate as output tokens ($0.50/1M)")