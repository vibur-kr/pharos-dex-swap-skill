# Pharos DEX Swap Skill

A Pharos Agent Center Skill that enables AI agents to swap tokens on Pharos through FaroSwap Uniswap V3 pools via natural language commands. Auto-executes swaps when safety checks pass — no confirmation dialogs unless something is wrong.

## Features

- **Auto-Execute Swaps** — Say "swap 100 USDC to PROS" and get the result. No confirmation dialogs when all safety checks pass (price impact < 3%, sufficient liquidity, sufficient balance).
- **Uniswap V3 Pools** — Swaps through FaroSwap V3 pools (0.01%, 0.05%, 0.3%, 1% fee tiers) via FaroSwap Router
- **Pool Auto-Discovery** — Instant pool discovery via V3 Factory `getPool()` (1-2 seconds, no scanning)
- **Multi-Pool Comparison** — Quotes all fee tiers and picks the best rate
- **Python V3 Math** — Off-chain quoting with pure integer arithmetic (no on-chain Quoter needed)
- **Liquidity Safety** — Checks pool liquidity before swapping. Skips empty pools. Rejects excessive swaps
- **Price Impact Guard** — Hard 3% threshold blocks bad trades. Override only after risk explanation
- **Exact-Amount Approvals** — Approves tokens for the exact swap amount only via DODO Approve Proxy
- **Slippage Protection** — 0.5% default slippage tolerance via `minReturnAmount`
- **Native Token Handling** — FaroSwap Router handles PROS wrapping/unwrapping automatically
- **Built-in Token Registry** — All official Pharos tokens with addresses from docs.pharos.xyz
- **Dual Network** — Pharos Atlantic Testnet and Pharos Pacific Mainnet with auto-configured RPC
- **Wallet Balance Check** — Query all token balances in one command
- **Send After Swap** — Swap tokens and send the result to any address in one request

## Installation

### One-line install (recommended)

```bash
npx skills add https://github.com/vibur-kr/pharos-dex-swap-skill
```

### Manual install

Copy the `pharos-dex-swap-skill` folder to your agent's skills directory:

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Codex | `~/.codex/skills/` |

Example for Claude Code:
```bash
cp -r pharos-dex-swap-skill ~/.claude/skills/
```

Skill files:
```
pharos-dex-swap-skill/
├── SKILL.md     — main skill file (instructions for the AI agent)
├── helpers.py   — Python V3 quote math + mixSwap calldata encoder
└── README.md    — this file
```

Restart your agent session after installing.

## First Launch

On first invocation the agent will:

1. Check that `cast` (Foundry) is installed
2. Create a `.env` file with a `PRIVATE_KEY` placeholder
3. Ask you to fill in your private key (in the `.env` file, never in chat)
4. Verify network connectivity (defaults to Pharos Pacific Mainnet)

## Environment Variables

All secrets are stored in the `.env` file. **Never paste keys directly into the chat.**

```bash
# Your wallet private key (without 0x prefix)
# SECURITY: Edit this file directly. Do NOT paste your key in chat.
PRIVATE_KEY=your_key_here
```

## Supported Tokens

### Atlantic Testnet

| Token | Address |
|-------|---------|
| WPHRS | `0x838800b758277CC111B2d48Ab01e5E164f8E9471` |
| USDC | `0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B` |
| USDT | `0xE7E84B8B4f39C507499c40B4ac199B050e2882d5` |
| WETH | `0x7d211F77525ea39A0592794f793cC1036eEaccD5` |
| WBTC | `0x0c64F03EEa5c30946D5c55B4b532D08ad74638a4` |

### Pacific Mainnet

| Token | Address |
|-------|---------|
| WPROS | `0x52c48d4213107b20bc583832b0d951fb9ca8f0b0` |
| USDC | `0xc879c018db60520f4355c26ed1a6d572cdac1815` |
| WETH | `0x1f4b7011Ee3d53969bb67F59428a9ec0477856E9` |
| LINK | `0x51e2A24742Db77604B881d6781Ee16B5b8fcBE29` |

Custom ERC20 tokens are also supported — provide the contract address when prompted.

## Usage Examples

```
"Swap 100 USDC to PROS on Pharos"             — Auto-executes, no confirmation
"Trade 0.5 PROS for USDC"                     — Native token swap, auto-executes
"Convert all my USDC to PROS"                 — Swap full balance
"Exchange 50 WPROS for USDC"                  — Large swap with impact check
"What's the rate for 100 USDC to PROS?"       — Quote only, no execution
"How much money do I have on Pharos?"          — Balance check
"Send 10 USDC to 0xABC123..."                 — Direct transfer
"Swap 10 PROS to USDC and send to 0xABC..."   — Auto-swap + send
```

## How It Works

### Swap (auto-execute flow)
1. **Parse** your request into token pair, amount, and network
2. **Discover** V3 pools via Factory `getPool()` for all fee tiers (1-2 seconds)
3. **Quote** each pool with Python V3 integer math, pick the best rate
4. **Safety check** — price impact < 3%, sufficient balance, sufficient liquidity
5. **All checks pass** → auto-execute (no confirmation). **Any check fails** → stop and explain
6. **Approve** exact swap amount via DODO Approve Proxy
7. **Execute** `mixSwap()` on FaroSwap Router with slippage protection
8. **Report** — tx hash, amounts, rate, and explorer link

### Balance Check
1. **Query** native token balance and all ERC20 balances from the token registry
2. **Report** non-zero holdings in human-readable format

### Send
1. **Validate** recipient address and check balance
2. **Confirm** amount and recipient with user
3. **Execute** native or ERC20 transfer
4. **Report** — tx hash and explorer link

## Architecture

```
User → FaroSwap Router (DODO RouteProxy) → V3 Adapter → Uniswap V3 Pool
         mixSwap(...)                        sellBase()      swap()
```

| Component | Address |
|-----------|---------|
| V3 Factory | `0x2c90CcB0b989afA2433F499698451a25744A552b` |
| FaroSwap Router | `0xA5cA5Fbe34e444F366B373170541ec6902b0F75c` |
| DODO Approve Proxy | `0x2aFc65f51B8afd1dB9618643F89f0b135EaAeEAa` |
| V3 Adapter | `0x4fd44181839d24e7c8f4d1b9288379109ec25fae` |

## Safety Features

| Feature | Detail |
|---------|--------|
| Auto-execute | Swaps run automatically when all safety checks pass |
| Exact approvals | Only the swap amount is approved — never `uint256.max` |
| Price impact guard | Hard block at 3% — override only after risk explanation |
| Liquidity check | Skip pools with 0 active liquidity |
| Slippage protection | 0.5% default — tx reverts if price moves beyond |
| No secret in chat | All keys via `.env` file only |

## Requirements

- [Foundry](https://book.getfoundry.sh/getting-started/installation) (`cast` command)
- Python 3 (for V3 quote math and calldata encoding)
- A Pharos wallet with PHRS/PROS for gas

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `cast` not found | Install: `curl -L https://foundry.paradigm.xyz \| bash && foundryup` |
| No pools found | Token pair may not have a V3 pool. Check available pairs on faroswap.xyz |
| Swap reverted | Price moved — get a fresh quote and retry |
| Insufficient gas | Wallet needs PHRS (testnet) or PROS (mainnet) |
| `.env` not loading | Use absolute path: `source /full/path/to/.env` |
| `python3` not found | Install Python 3 or try `python` instead |

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.
