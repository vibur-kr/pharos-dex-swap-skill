# Pharos DEX Swap Skill

A Pharos Agent Center Skill that enables AI agents to swap tokens on Pharos DEX pools (FaroSwap, Zenith, and custom DODO-based pools) through natural language commands.

## Features

- **Natural Language Swap** — "Swap 100 USDC to WPHRS on Pharos" and the agent handles everything
- **Pool Auto-Discovery** — Automatically finds all DODO-based pools for a token pair by scanning on-chain data
- **Multi-Pool Comparison** — Quotes all available pools and picks the best rate
- **Liquidity Safety** — Checks pool reserves before swapping. Skips empty or low-liquidity pools. Rejects swaps exceeding 10% of pool reserves
- **Price Impact Guard** — Hard 3% threshold blocks bad trades. User can override only after reading a clear risk explanation
- **Exact-Amount Approvals** — Approves tokens for the exact swap amount only. No unlimited spending, ever
- **Slippage Protection** — 0.5% default slippage tolerance. Transaction reverts if price moves unfavorably
- **Native Token Handling** — Automatically wraps PHRS/PROS before swapping and unwraps after
- **Built-in Token Registry** — All official Pharos tokens (WPHRS, USDC, USDT, WETH, WBTC, LINK) with addresses from docs.pharos.xyz
- **Dual Network** — Pharos Atlantic Testnet and Pharos Pacific Mainnet with auto-configured RPC and explorer URLs

## Installation

npx skills add https://github.com/vibur-kr/pharos-dex-swap-skill

or manually

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
├── SKILL.md    — main skill file (instructions for the AI agent)
└── README.md   — this file
```

Restart your agent session after installing.

## First Launch

On first invocation the agent will:

1. Check that `cast` (Foundry) is installed
2. Create a `.env` file with a `PRIVATE_KEY` placeholder
3. Ask you to fill in your private key (in the `.env` file, never in chat)
4. Verify network connectivity

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
"Swap 100 USDC to WPHRS on Pharos"
"Trade 0.5 PHRS for USDC on testnet"
"Convert all my USDT to WPHRS"
"Exchange 50 USDC for USDT on Pharos mainnet"
"What's the rate for 100 USDC to WPHRS?"
```

## How It Works

1. **Parse** your request into token pair, amount, and network
2. **Discover** all DODO-based pools for the pair by scanning on-chain Transfer events
3. **Filter** pools by liquidity — skip empty pools, reject swaps > 10% of reserves
4. **Quote** each valid pool, calculate price impact, select the best rate
5. **Confirm** — show quote with rate, reserves, and price impact for your approval
6. **Approve** the exact swap amount only (never unlimited)
7. **Execute** the swap with slippage protection
8. **Report** — tx hash, amounts, and explorer link

## Safety Features

| Feature | Detail |
|---------|--------|
| Exact approvals | Only the swap amount is approved — never `uint256.max` |
| Price impact guard | Hard block at 3% — override only after risk explanation |
| Reserve check | Reject if swap > 10% of pool reserves |
| Slippage protection | 0.5% default — tx reverts if price moves beyond |
| No secret in chat | All keys via `.env` file only |

## Requirements

- [Foundry](https://book.getfoundry.sh/getting-started/installation) (`cast` command)
- A Pharos wallet with PHRS/PROS for gas

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `cast` not found | Install: `curl -L https://foundry.paradigm.xyz \| bash && foundryup` |
| No pools found | Token pair may not be traded. Check available pairs on faroswap.xyz |
| Swap reverted | Price moved — get a fresh quote and retry |
| Insufficient gas | Wallet needs PHRS (testnet) or PROS (mainnet) |
| `.env` not loading | Use absolute path: `source /full/path/to/.env` |

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.
