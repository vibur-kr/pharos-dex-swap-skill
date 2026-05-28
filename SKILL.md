---
name: pharos-dex-swap-skill
description: Pharos DEX token swap via FaroSwap Uniswap V3 pools. Single-command swap/balance/send — helpers.py handles pool discovery, V3 quoting, wrapping, approval and execution automatically. Auto-executes swaps when safety checks pass.
version: 2.0.0
frameworks:
  - openclaw
  - claude-code
  - codex
tags:
  - dex
  - swap
  - trade
  - faroswap
  - uniswap-v3
  - v3
  - amm
  - liquidity
  - price-impact
  - slippage
  - token-approval
  - exact-approve
  - wrap
  - balance
  - wallet
  - send
  - transfer
  - pharos
  - phrs
  - pros
  - wphrs
  - usdc
  - usdt
  - weth
  - foundry
  - cast
networks:
  - pharos-testnet
  - pharos-mainnet
---

# Pharos DEX Swap

Swap tokens on Pharos through FaroSwap Uniswap V3 pools. One command does everything — pool discovery, quoting, wrapping, approval, and execution. The user says "swap 10 PROS to USDC" and gets the result. Only stops for problems (price impact, insufficient liquidity, low balance).

Also supports wallet balance checks and direct token transfers (native and ERC20).

## Built-in Network Configuration

The skill knows Pharos network details. The agent does NOT need the user to provide RPC URLs or chain IDs.

### Pharos Atlantic Testnet

| Parameter | Value |
|-----------|-------|
| Network name | Pharos Atlantic Testnet |
| Chain ID | 688689 (0xa8231) |
| Currency | PHRS |
| RPC URL | `https://atlantic.dplabs-internal.com` |
| Block Explorer | `https://atlantic.pharosscan.com` |
| Token Explorer | `https://pharos-testnet.socialscan.io` |

### Pharos Pacific Mainnet

| Parameter | Value |
|-----------|-------|
| Network name | Pharos Pacific Mainnet |
| Chain ID | auto-detected via `cast chain-id` |
| Currency | PROS |
| RPC URL | `https://rpc.pharos.xyz` (fallback: `https://infra.originstake.com/pharos/evm`) |
| Block Explorer | `https://www.pharosscan.xyz` |

When the user selects or mentions a network, the agent MUST set these variables for the current session:
- `PHAROS_RPC_URL` — the RPC URL
- `PHAROS_NETWORK` — the network name
- `PHAROS_CHAIN_ID` — the chain ID
- `PHAROS_EXPLORER` — the block explorer URL
- `NATIVE_TOKEN` — `PHRS` for testnet, `PROS` for mainnet
- `WRAPPED_NATIVE` — `WPHRS` for testnet, `WPROS` for mainnet

If the user does not specify a network, default to **Pharos Pacific Mainnet**. Use testnet only when the user explicitly mentions "testnet", "atlantic", "test tokens", or asks about test balances.

## Built-in Token Registry

All token addresses below are from the official Pharos documentation at `docs.pharos.xyz/getting-started/token-registry`.

### Atlantic Testnet Tokens

| Symbol | Name | Decimals | Address |
|--------|------|----------|---------|
| WPHRS | Wrapped PHRS | 18 | `0x838800b758277CC111B2d48Ab01e5E164f8E9471` |
| USDC | USD Coin | 6 | `0xcfC8330f4BCAB529c625D12781b1C19466A9Fc8B` |
| USDT | Tether USD | 6 | `0xE7E84B8B4f39C507499c40B4ac199B050e2882d5` |
| WETH | Wrapped ETH | 18 | `0x7d211F77525ea39A0592794f793cC1036eEaccD5` |
| WBTC | Wrapped BTC | 18 | `0x0c64F03EEa5c30946D5c55B4b532D08ad74638a4` |

### Pacific Mainnet Tokens

| Symbol | Name | Decimals | Address |
|--------|------|----------|---------|
| WPROS | Wrapped PROS | 18 | `0x52c48d4213107b20bc583832b0d951fb9ca8f0b0` |
| USDC | USDC (Circle) | 6 | `0xc879c018db60520f4355c26ed1a6d572cdac1815` |
| WETH | Wrapped ETH | 18 | `0x1f4b7011Ee3d53969bb67F59428a9ec0477856E9` |
| LINK | Chainlink Token | 18 | `0x51e2A24742Db77604B881d6781Ee16B5b8fcBE29` |

### Token Resolution Rules

When the user mentions a token by symbol (e.g., "USDC", "ETH", "PHRS"):

1. **Native tokens** — `PHRS`, `PROS`, `ETH` (as native) → the native gas token. Address is `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEEeeEEEeE`. Must be wrapped before swapping through DEX pools. The FaroSwap Router handles wrapping automatically for native token swaps.
2. **Wrapped native** — `WPHRS`, `WPROS` → use the address from the registry above.
3. **Known tokens** — `USDC`, `USDT`, `WETH`, `WBTC`, `LINK` → use the address from the registry for the selected network.
4. **Custom tokens** — if the symbol is not in the registry, ask the user for the contract address. Verify it is a valid ERC20 by calling `name()`, `symbol()`, `decimals()`.

## Capabilities

- **Token Swap** — Swap any ERC20 token for another through Uniswap V3 pools on Pharos via FaroSwap Router.
- **Auto-Execution** — Swaps execute automatically without user confirmation when all safety checks pass (price impact < 3%, sufficient liquidity, sufficient balance). Only stops and asks the user if a safety check fails.
- **Pool Auto-Discovery** — Find all V3 pools for a token pair via Factory `getPool()` with fee tiers 100, 500, 3000, 10000. Instant (1-2 seconds).
- **Liquidity Safety Check** — Verify pool liquidity before quoting. Skip empty pools. Reject swaps that exceed 10% of pool liquidity.
- **Price Impact Guard** — Hard threshold (default 3%) that blocks swaps with excessive price impact. User can override only after reading a clear risk explanation.
- **Python V3 Quote** — Off-chain V3 math using pure integer arithmetic (no on-chain Quoter contract needed). Accurate for swaps that don't cross ticks.
- **Exact-Amount Approval** — Approve tokens for the exact swap amount only via DODO Approve Proxy. NEVER approve unlimited spending.
- **Slippage Protection** — Enforce minimum output amount via `minReturnAmount` in mixSwap. Transaction reverts if price moves beyond tolerance (default 0.5%).
- **Native Token Handling** — FaroSwap Router handles wrapping/unwrapping automatically when using `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEeEe` as fromToken/toToken.
- **Multi-Pool Comparison** — Quote all fee tiers (0.01%, 0.05%, 0.3%, 1%) and pick the best rate.
- **Wallet Balance Check** — Query native token balance and all known ERC20 token balances. Report only non-zero holdings in human-readable format.
- **Send After Swap** — Optionally send swapped tokens to a specified address after the swap completes.

## Known DEX Contracts on Pharos

The agent MUST use these known contract addresses. No scanning or discovery scanning is needed for pool discovery — use V3 Factory `getPool()` instead.

### Pacific Mainnet

| Component | Address | Purpose |
|-----------|---------|---------|
| V3 Factory | `0x2c90CcB0b989afA2433F499698451a25744A552b` | Pool discovery via `getPool()` |
| FaroSwap Router | `0xA5cA5Fbe34e444F366B373170541ec6902b0F75c` | Swap execution via `mixSwap()` |
| DODO Approve Proxy | `0x2aFc65f51B8afd1dB9618643F89f0b135EaAeEAa` | Token approvals for swaps |
| V3 Adapter | `0x4fd44181839d24e7c8f4d1b9288379109ec25fae` | Adapter between Router and V3 Pools |

### V3 Fee Tiers

Always check all four tiers when discovering pools:

| Fee | Tick Spacing | Use Case |
|-----|-------------|----------|
| 100 | 1 | Stablecoin pairs |
| 500 | 10 | Low-volatility pairs |
| 3000 | 60 | Standard pairs |
| 10000 | 200 | Exotic / high-volatility pairs |

### Native Token Convention

- `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEeEe` — represents native PROS/PHRS in mixSwap calls
- WPROS = `0x52c48d4213107b20bc583832b0d951fb9ca8f0b0`
- USDC = `0xc879c018db60520f4355c26ed1a6d572cdac1815`

## Uniswap V3 Function Reference

### V3 Factory

```
getPool(address tokenA, address tokenB, uint24 fee)(address pool)
```

Returns the pool address for a token pair and fee tier. Returns `0x000...000` if no pool exists.

### V3 Pool

```
token0()(address)
token1()(address)
fee()(uint24)
tickSpacing()(int24)
slot0()(uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)
liquidity()(uint128)
```

### FaroSwap Router (DODO RouteProxy)

```
mixSwap(
  address fromToken,
  address toToken,
  uint256 fromTokenAmount,
  uint256 minReturnAmount,
  uint256 expectedAmount,
  address[] mixAdapters,
  address[] assetIds,
  address[] pathIds,
  uint256 directions,
  bytes[] extraData,
  bytes userData,
  uint256 deadline
)(uint256 receiveAmount)
```

**Parameter details for V3 single-hop swap:**

| Parameter | Value |
|-----------|-------|
| fromToken | input token address (`0xEeeee...` for native) |
| toToken | output token address (`0xEeeee...` for native) |
| fromTokenAmount | input amount in raw units |
| minReturnAmount | minimum output (slippage protection) |
| expectedAmount | quoted expected output |
| mixAdapters | `[V3_ADAPTER]` — single element array |
| assetIds | `[POOL_ADDRESS]` — the V3 pool |
| pathIds | `[V3_ADAPTER, ROUTER]` — two elements |
| directions | `0` if fromToken < toToken (selling token0), `1` if fromToken > toToken (selling token1). Determined by `token0()` of the pool. |
| extraData | `[abi.encode(uint256(0xc0))]` — constant bytes array |
| userData | `abi.encode(uint256(0), uint256(0))` — 64 zero bytes |
| deadline | unix timestamp + 600 (10 min from now) |

### DODO Approve Proxy

```
isAllowedProxy(address)(bool)
```

### ERC20 Functions

```
balanceOf(address)(uint256)
allowance(address owner, address spender)(uint256)
approve(address spender, uint256 amount)(bool)
symbol()(string)
decimals()(uint8)
```

### Wrapped Native Functions (WPHRS / WPROS)

```
deposit()     — wrap native token (send PHRS/PROS with this call)
withdraw(uint256 amount) — unwrap to native token
```

### Transfer Functions

```
# ERC20 transfer
transfer(address to, uint256 amount)(bool)

# Native token transfer (via cast send)
cast send $RECIPIENT --value $AMOUNT --rpc-url $RPC --private-key $KEY --legacy
```

## Capability: Balance Check

The agent can check wallet balances independently of swaps. Trigger this when the user asks about their balance, portfolio, or holdings.

### Step B.1: Run Balance Command

```bash
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py balance --network $NETWORK
```

### Step B.2: Parse Result

JSON output:
```json
{
  "success": true,
  "action": "balance",
  "wallet": "0x...",
  "balances": {
    "PROS": 1.5,
    "USDC": 100.0
  },
  "network": "mainnet"
}
```

Present to user:
```
Wallet: {wallet} on {network}

  PROS:  1.500000
  USDC:  100.000000
```

## Capability: Send Transaction

The agent can send native tokens or ERC20 tokens to any address. This works **standalone** (user says "send 10 USDC to 0x...") and also **after swaps** (Step 2.4).

**IMPORTANT: Sending tokens ALWAYS requires user confirmation** (unlike swaps which auto-execute). Show the amount and recipient before sending.

### Step S.1: Parse Send Request

Extract from the user's message:

| Parameter | Example | Required |
|-----------|---------|----------|
| `token` | USDC, PHRS, WETH | Yes |
| `amount` | 10, 0.5 | Yes |
| `recipient` | 0xABC... | Yes |
| `network` | testnet, mainnet | No (default: mainnet) |

### Step S.2: Confirm with User

```
Send {amount} {token} to {recipient} on {network}?

1. Yes, send now
2. Cancel
```

**NEVER send without user confirmation.**

### Step S.3: Run Send Command

```bash
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py send --token $TOKEN --amount $AMOUNT --to $RECIPIENT --network $NETWORK
```

The command handles native and ERC20 transfers automatically, including balance check.

### Step S.4: Parse Result

JSON output:
```json
{
  "success": true,
  "action": "send",
  "token": "USDC",
  "amount": 10.0,
  "to": "0xABC...",
  "txHash": "0xdef456...",
  "explorer": "https://pharosscan.xyz/tx/0xdef456..."
}
```

Present to user:
```
Sent!

  {amount} {token} -> {recipient}
  TX: {explorer}
```

## Phase 0: Setup (run once per session)

This phase runs automatically every time the skill is invoked.

### Step 0.1: Environment File Setup

**Determine project root:**

```bash
PROJECT_ROOT=$(pwd)
ENV_FILE="$PROJECT_ROOT/.env"
```

The agent MUST determine the absolute path to the project root once and reuse it for ALL subsequent commands. Store `ENV_FILE` as the absolute path to `.env`.

1. Check if `.env` exists at the project root:

```bash
[ -f "$ENV_FILE" ] && echo ".env exists at: $ENV_FILE" || echo ".env not found"
```

2. If `.env` does NOT exist, create it:

```bash
cat > "$ENV_FILE" << 'ENVEOF'
# ============================================
# Pharos DEX Swap — Environment Variables
# ============================================
# Fill in your values below. NEVER share this file or commit it to git.
# ============================================

# Your wallet private key (without 0x prefix)
# SECURITY: Edit this file directly. Do NOT paste your key in chat.
PRIVATE_KEY=

# Network will be selected automatically or by user request.
# No need to set RPC URL manually.
ENVEOF
echo ".env created at: $ENV_FILE"
```

3. Ensure `.env` is in `.gitignore`:

```bash
GITIGNORE="$PROJECT_ROOT/.gitignore"
[ -f "$GITIGNORE" ] && grep -qxF '.env' "$GITIGNORE" || echo '.env' >> "$GITIGNORE"
```

**CRITICAL — Shell state does NOT persist between Bash tool calls.** Every command MUST:
- Source `.env` using the **absolute path**: `set -a && source $ENV_FILE && set +a && ...rest...`
- NEVER use relative `source .env` — it breaks if CWD changes
- The `$ENV_FILE` variable does NOT persist either — the agent MUST re-determine or hardcode the absolute path in every command

### Step 0.2: Locate helpers.py

The skill requires `helpers.py` for ALL operations (swap, balance, send). It MUST be in the same directory as SKILL.md.

The agent MUST determine the absolute path to the skill directory (where SKILL.md is located) and store it as `SKILL_DIR`. Then `SKILL_DIR/helpers.py` is the helpers path.

Common paths:
- Claude Code: `~/.claude/skills/pharos-dex-swap-skill/helpers.py`
- OpenClaw: `~/.openclaw/skills/pharos-dex-swap-skill/helpers.py`

```bash
[ -f "$SKILL_DIR/helpers.py" ] && echo "helpers.py found" || echo "helpers.py NOT found"
```

If not found → the skill is installed incorrectly. The user must ensure `helpers.py` is in the same folder as `SKILL.md`.

### Step 0.3: Verify Private Key

Check if PRIVATE_KEY is set. **ONLY output "yes" or "no" — never the actual value.**

```bash
set -a && source $ENV_FILE && set +a && [ -n "$PRIVATE_KEY" ] && echo "PRIVATE_KEY: set" || echo "PRIVATE_KEY: not set"
```

**FORBIDDEN COMMANDS — NEVER RUN THESE:**
```
cat .env
echo $PRIVATE_KEY
printenv PRIVATE_KEY
head .env
grep PRIVATE_KEY .env
```
Any command that would output the private key value to chat is ABSOLUTELY FORBIDDEN.

If not set, guide the user:

```
Please open the .env file and add your private key:
  File: {absolute_path_to_.env}

Set: PRIVATE_KEY=your_key_here (with or without 0x prefix)

NEVER paste keys in chat.
```

After the user confirms they filled in the key, normalize it (strip 0x prefix if present):

```bash
sed -i 's/^PRIVATE_KEY=0[xX]\(.*\)/PRIVATE_KEY=\1/' "$ENV_FILE"
```

### Step 0.4: Check Dependencies (quick check)

```bash
cast --version || $HOME/.foundry/bin/cast --version
python3 --version || python --version
```

If `cast` not found → offer to install Foundry. If Python not found → ask user to install Python 3.

### Security Rules (CRITICAL — enforce at all times)

1. **NEVER** output, display, echo, print, cat, grep, or log the value of PRIVATE_KEY or any secret
2. **NEVER** ask the user to paste private keys or secrets in chat
3. **NEVER** run `cat .env`, `echo $PRIVATE_KEY`, `printenv`, `grep PRIVATE_KEY`, or any command that could leak secrets to chat output
4. **ALWAYS** check .env with safe commands only: `[ -n "$PRIVATE_KEY" ] && echo "set" || echo "not set"`
5. **ALWAYS** show the full absolute path to the `.env` file so the user can find it
6. **NEVER** approve unlimited token spending — exact swap amount only
7. If the user accidentally pastes a secret in chat — warn immediately, suggest rotating the key

## Shell State Note (CRITICAL)

Shell state does NOT persist between Bash tool calls. EVERY command that uses env vars MUST source `.env` with the **absolute path** determined in Step 0.1:

```bash
set -a && source /absolute/path/to/.env && set +a && ...rest of command...
```

## Phase 1: Parse Intent

Parse the user's natural language request into structured parameters.

### Step 1.1: Extract Parameters

From the user's message, extract:

| Parameter | Example | Required |
|-----------|---------|----------|
| `tokenIn` | USDC, PHRS, WETH | Yes |
| `amountIn` | 100, 0.5, all | Yes |
| `tokenOut` | WPHRS, USDT, WBTC | Yes |
| `sendTo` | 0xABC..., send to... | No |
| `network` | testnet, mainnet | No (default: mainnet) |

If the user mentions "send to", "send ... to 0x", "transfer to", or provides an address after "swap" — extract `sendTo` as the recipient address.

### Step 1.2: Resolve Network

If the user mentions "testnet", "atlantic", or asks about test tokens → `testnet`.
If the user mentions "mainnet", "pacific", or "PROS" as native → `mainnet`.
Default: **mainnet**.

### Step 1.3: Proceed to Execute

The agent does NOT need to resolve token addresses or convert amounts — `helpers.py` handles all of that. Just pass the user's token symbols and amount directly to the command.

## Phase 2-6: Execute Swap (Single Command)

**CRITICAL: All swap logic is handled by a single Python command.** The agent does NOT run multiple `cast` calls, pool discovery, quoting, or encoding separately. Everything happens inside `helpers.py swap`.

### Step 2.1: Run the Swap Command

The `helpers.py swap` command handles the entire flow:
1. Resolves token symbols to addresses
2. Finds the pool (hardcoded primary pool for WPROS/USDC, Factory discovery fallback for others)
3. Reads pool state (`slot0`, `liquidity`)
4. Quotes using V3 math
5. Checks safety (price impact < 3%, sufficient balance, liquidity > 0)
6. Wraps native tokens if needed (PROS → WPROS)
7. Approves exact amount via DODO Approve Proxy
8. Encodes `mixSwap` calldata
9. Executes the swap
10. Returns JSON result

**Single command:**

```bash
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py swap --from $TOKEN_IN --to $TOKEN_OUT --amount $AMOUNT --network $NETWORK
```

Examples:
```bash
# Swap 10 PROS to USDC on mainnet
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py swap --from PROS --to USDC --amount 10 --network mainnet

# Swap 50 USDC to WPROS on mainnet
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py swap --from USDC --to WPROS --amount 50 --network mainnet

# Swap all USDC to PROS on mainnet
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py swap --from USDC --to PROS --amount all --network mainnet

# Swap on testnet
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py swap --from USDC --to WPHRS --amount 100 --network testnet
```

### Step 2.2: Parse the JSON Result

The command outputs JSON to stdout. Progress messages go to stderr (visible to user but not parsed).

**Success output:**
```json
{
  "success": true,
  "action": "swap",
  "from": "PROS",
  "to": "USDC",
  "amountIn": 10.0,
  "amountOut": 6.273717,
  "rate": 0.627372,
  "priceImpactBps": 1,
  "pool": "0x912c9aDe...",
  "fee": 100,
  "txHash": "0xabc123...",
  "explorer": "https://pharosscan.xyz/tx/0xabc123..."
}
```

**Error output (exit code 1):**
```json
{
  "error": "Price impact too high: 4.50% > 3%. Try a smaller amount."
}
```

### Step 2.3: Handle the Result

**On success** — present to the user:
```
Swap complete!

  Sent:       {amountIn} {from}
  Received:   {amountOut} {to}
  Rate:       1 {from} = {rate} {to}
  Pool:       {pool} ({fee/10000}% fee)
  Price impact: {priceImpactBps/100}%

  TX: {explorer}
```

**On error** — show the error and offer options:
```
Swap failed: {error message}

1. Try a different amount or token
2. Cancel
```

### Step 2.4: Send Swapped Tokens (if requested)

If the user's original request included a recipient (e.g., "swap 10 PROS to USDC and send to 0x..."), run:

```bash
set -a && source $ENV_FILE && set +a && python3 $SKILL_DIR/helpers.py send --token $TOKEN_OUT --amount $AMOUNT_OUT --to $RECIPIENT --network $NETWORK
```

The `send` command handles native and ERC20 transfers automatically.

### How helpers.py Swap Works Internally

The agent does NOT need to know these details, but for reference:

1. **Pool lookup**: Checks hardcoded pool registry first (instant, no RPC calls). Falls back to Factory `getPool()` for unknown pairs.
2. **Quote**: Reads `slot0` + `liquidity` from pool (2 RPC calls), computes output with Python V3 integer math.
3. **Safety**: Blocks if price impact > 3%, liquidity = 0, or balance insufficient.
4. **Native token**: Wraps PROS → WPROS via `deposit()`, approves exact amount, swaps as WPROS.
5. **Execution**: Encodes `mixSwap` calldata, sends via `cast send` with 0.5% slippage protection.
6. **All steps** run in a single process — one command, one terminal approval, zero back-and-forth.

## Language Rule

The agent MUST communicate with the user in the **same language the user uses**. Detection: use the language of the user's most recent message. Technical terms (variable names, commands, function names, token symbols) remain in English regardless.

## Error Handling

| Issue | Solution |
|-------|----------|
| `cast` not found | Install Foundry: `curl -L https://foundry.paradigm.xyz \| bash && foundryup` |
| RPC unreachable | For mainnet, try fallback RPC. For testnet, check the URL. |
| No pools found | The token pair may not be traded on any Pharos V3 pool. Suggest available pairs. |
| All pools have 0 liquidity | No active liquidity in current tick. Inform user, suggest different fee tier or waiting. |
| Quote returns 0 | Swap amount may be too small, or pool state is unusual. Check amount and decimals. |
| Approve fails | Check that PRIVATE_KEY is correct and wallet has PROS for gas. |
| Swap reverts (slippage) | Price moved. Get a fresh quote and retry, or increase slippage. |
| Swap reverts (direction) | Check `direction` parameter — must match pool's token0/token1 ordering. |
| Send fails (transfer) | Check token balance and gas. Verify recipient address. |
| Insufficient gas | Wallet needs PHRS (testnet) or PROS (mainnet) for transaction fees. |
| `.env` not loading | Use absolute path: `source /full/path/to/.env` |
| `python3` not found | The helper script requires Python 3. Install or use `python` instead. |
| cast can't parse `0xEeeee...` | Use lowercase: `0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee` in cast calls |

## Example Usage Prompts

### Swaps (auto-execute, no confirmation needed)
1. **"Swap 100 USDC to PROS on Pharos"** — Standard swap, auto-executes
2. **"Trade 0.5 PROS for USDC"** — Native token swap via FaroSwap Router, auto-executes
3. **"Convert all my USDC to PROS"** — Swap full balance, auto-executes
4. **"Exchange 1000 WPROS for USDC"** — Large swap with impact check
5. **"What's the rate for 100 USDC to PROS?"** — Quote only, no execution

### Balance Check
6. **"How much money do I have on Pharos?"** — Balance check (all tokens)
7. **"Show my Pharos wallet balance"** — Balance check

### Send
8. **"Send 10 USDC to 0xABC..."** — Direct ERC20 transfer
9. **"Send 0.5 PROS to 0xABC..."** — Direct native transfer

### Combined (Swap + Send)
10. **"Swap 10 PROS to USDC and send to 0xABC..."** — Auto-swap + send to address
11. **"Convert 50 USDC to WPROS and send to 0xABC..."** — Auto-swap + send
