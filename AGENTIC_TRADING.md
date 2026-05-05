# Agentic Trading Platform

> Multi-LLM autonomous trading bot with strict portfolio guardrails

## Goal

Build a fully autonomous trading agent that:
- Uses multiple LLMs (OpenAI, Anthropic, Groq, etc.) for specialized analysis
- Makes independent buy/sell decisions through Alpaca
- Enforces strict risk management rules that cannot be overridden
- Runs as an experiment with a capped investment amount (e.g., $5k)

---

## Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC TRADING PLATFORM                     │
├─────────────────────────────────────────────────────────────────┤
│  GUARDRAILS (Hard Limits - Cannot Be Overridden)                │
│  ├── Position Limits    ├── Loss Limits    ├── Kill Switch     │
├─────────────────────────────────────────────────────────────────┤
│  LLM ROUTER (Multi-Model Support)                               │
│  ├── GPT-4o    ├── Claude    ├── Groq/Llama    ├── Mistral     │
├─────────────────────────────────────────────────────────────────┤
│  SPECIALIZED AGENTS (Run in Parallel)                           │
│  ├── Research Agent      → Fundamentals, financials, news       │
│  ├── Technical Agent     → Price patterns, indicators           │
│  ├── Sentiment Agent     → Social media, analyst ratings        │
│  └── Risk Agent          → Volatility, position sizing          │
├─────────────────────────────────────────────────────────────────┤
│  DECISION SYNTHESIZER                                           │
│  └── Merges all agent outputs → Final BUY/SELL/HOLD decision    │
├─────────────────────────────────────────────────────────────────┤
│  EXECUTION (Alpaca)                                             │
│  └── Paper Trading → Live Trading (when ready)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Strict Portfolio Rules (Guardrails)

These are **hard-coded limits** that no LLM can override:

### Position Limits
| Rule | Limit |
|------|-------|
| Max single stock position | **5%** of portfolio |
| Max sector exposure | **20%** of portfolio |
| Max total positions | 30 stocks |
| Min cash reserve | 5% always in cash |

### Risk Limits
| Rule | Limit |
|------|-------|
| Max single trade | $500 |
| Max daily loss | **3%** → auto-pause trading |
| Max total drawdown | **15%** → auto-kill trading |
| Max daily trades | 15 |

### Execution Rules
| Rule | Behavior |
|------|----------|
| Confidence threshold | Minimum 0.65 to execute |
| Agent consensus | At least 2 agents must agree |
| Risk agent veto | Risk agent can block any trade |

---

## Agent Responsibilities

| Agent | Model Preference | Task |
|-------|-----------------|------|
| **Research** | GPT-4o (reasoning) | Analyze fundamentals, earnings, news |
| **Technical** | Groq/Llama (speed) | Chart patterns, RSI, MACD, trends |
| **Sentiment** | Claude Haiku (balance) | Social buzz, analyst ratings |
| **Risk** | Claude Sonnet (careful) | Position sizing, risk assessment |
| **Synthesizer** | Best available | Final decision from all inputs |

---

## Safety Features

### Kill Switch
- **Manual**: Stop all trading instantly from dashboard
- **Auto-trigger**: Activates at 15% total drawdown

### Pause Mode
- **Manual**: Temporarily halt trading
- **Auto-trigger**: Activates at 3% daily loss
- **Cooldown**: 60-minute pause after loss trigger

### Audit Trail
- Every decision logged with full reasoning
- All agent outputs preserved
- Complete trade history

---

## New File Structure

```
micro-investing/
├── core/
│   ├── agents/                    # NEW
│   │   ├── base.py                # Base agent class
│   │   ├── research_agent.py      # Fundamental analysis
│   │   ├── technical_agent.py     # Technical analysis
│   │   ├── sentiment_agent.py     # Sentiment analysis
│   │   ├── risk_agent.py          # Risk assessment
│   │   └── synthesizer.py         # Decision merger
│   │
│   ├── clients/
│   │   ├── alpaca.py              # EXISTING
│   │   └── llm/                   # NEW
│   │       ├── registry.py        # Model registry & toggling
│   │       ├── openai_client.py
│   │       ├── anthropic_client.py
│   │       └── groq_client.py
│   │
│   ├── data/                      # NEW
│   │   └── provider.py            # Market data aggregator
│   │
│   ├── safety/                    # NEW
│   │   ├── guardrails.py          # Hard limits
│   │   └── kill_switch.py         # Emergency stop
│   │
│   ├── orchestrator.py            # NEW - Main controller
│   │
│   └── strategies/                # EXISTING
│       └── agentic.py             # NEW - Agentic strategy
│
├── dashboard/                     # NEW
│   └── app.py                     # Monitoring UI
│
└── data/
    └── state/                     # State persistence
        ├── guardrails_state.json
        └── session_logs/
```

---

## API Keys Required

| Service | Purpose |
|---------|---------|
| OpenAI | GPT-4o, GPT-4o-mini |
| Anthropic | Claude Sonnet, Haiku |
| Groq | Fast Llama inference |
| Alpaca | Trading + market data |

---

## Workflow

1. **Scheduler triggers** trading cycle (hourly during market hours)
2. **Data layer** gathers market data, news, sentiment
3. **Agents run in parallel** - each analyzes from their specialty
4. **Synthesizer merges** all opinions into unified decision
5. **Guardrails validate** the proposed trade
6. **Execute or reject** based on rules
7. **Log everything** for review

---

## Getting Started

```bash
# 1. Set environment variables
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export ALPACA_API_KEY="..."
export ALPACA_SECRET_KEY="..."

# 2. Start with paper trading
python agentic_runner.py --paper --dry-run

# 3. Monitor via dashboard
python dashboard/app.py
```

---

## Experiment Setup

For a $5,000 experiment over 1 month:
- Start in paper trading mode
- Set `max_total_investment: 5000`
- Enable all guardrails
- Monitor daily via dashboard
- Review agent reasoning for learning

---

## Philosophy

> **The agents decide WHAT to buy. The guardrails decide HOW MUCH.**

- No symbol restrictions - agents have full universe
- Strict position/sector limits prevent concentration risk
- Multiple perspectives reduce single-model bias
- Hard stops protect capital from catastrophic loss

