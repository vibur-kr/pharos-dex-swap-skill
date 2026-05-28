---
name: pharos-dex-swap-skill
description: Pharos DEX token swap via FaroSwap Uniswap V3 pools — auto-discovers pools via V3 Factory, quotes with Python V3 math, executes through FaroSwap Router mixSwap. Also supports wallet balance checks and token transfers. Auto-executes swaps when safety parameters are within bounds.
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

Swap tokens on Pharos through FaroSwap Uniswap V3 pools. The skill auto-discovers pools via V3 Factory `getPool()`, quotes using Python V3 math (no on-chain Quoter needed), and executes swaps through FaroSwap Router `mixSwap()`. Runs fully automatic — the user says "swap X to Y" and gets the result. Only stops for problems (price impact, insufficient liquidity, low balance).

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

### Step B.1: Determine Network

Same rules as Phase 1.3 — detect from user's message or default to mainnet.

### Step B.2: Check Native Token Balance

```bash
set -a && source $ENV_FILE && set +a && cast balance $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

Convert from wei to human-readable:

```bash
cast from-wei $BALANCE
```

### Step B.3: Check ERC20 Token Balances

For each token in the Built-in Token Registry for the selected network:

```bash
set -a && source $ENV_FILE && set +a && cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

Convert from raw units to human-readable using the token's decimals:

```bash
echo "scale=6; $RAW_BALANCE / (10 ^ $DECIMALS)" | bc
```

### Step B.4: Report Results

Show only tokens with non-zero balance. Format:

```
Wallet: {walletAddress} on {network}

  {NATIVE_TOKEN}:  {balance} (approx ${usdValue} if known)
  USDC:   {balance}
  WETH:   {balance}
  ...

Total tokens: {count}
```

If all balances are zero: "Your wallet has no tokens on {network}. You may need to request tokens from a faucet."

## Capability: Send Transaction

The agent can send native tokens or ERC20 tokens to any address. This works **standalone** (user says "send 10 USDC to 0x...") and also **after swaps** (Phase 5.7). No swap or balance check required — just send.

### Step S.1: Parse Send Request

Extract from the user's message:

| Parameter | Example | Required |
|-----------|---------|----------|
| `token` | USDC, PHRS, WETH | Yes |
| `amount` | 10, 0.5 | Yes |
| `recipient` | 0xABC... | Yes |
| `network` | testnet, mainnet | No (default: mainnet) |

Resolve the token address from the Built-in Token Registry. If native token (PHRS/PROS) — send as native. Otherwise — send as ERC20.

Convert amount to wei using the token's decimals.

### Step S.2: Validate Recipient Address

```bash
cast --to-checksum-address $RECIPIENT
```

If this fails → "Invalid address. Please provide a valid 0x address."

### Step S.3: Check Balance

```bash
# For ERC20
set -a && source $ENV_FILE && set +a && cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL

# For native token
set -a && source $ENV_FILE && set +a && cast balance $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

If balance < amount:

```
Insufficient balance.

  Token:    {token}
  Send:     {amount}
  Balance:  {balance}

1. Send {balance} instead (max available)
2. Cancel
```

For native token sends, also check that enough remains for gas:

```
Balance:  {balance} {NATIVE_TOKEN}
Send:     {amount} {NATIVE_TOKEN}
Gas est:  ~{gasEstimate} {NATIVE_TOKEN}
Remaining after send + gas: {remaining}

{if remaining < 0:} Not enough for gas. Reduce send amount.
```

### Step S.4: Confirm with User

```
Send {amount} {token} to {recipient} on {network}?

  From:     {walletAddress}
  To:       {recipient}
  Amount:   {amount} {token}

1. Yes, send now
2. Cancel
```

**NEVER send without user confirmation.**

### Step S.5: Execute Send

**Native token (PHRS / PROS):**

```bash
set -a && source $ENV_FILE && set +a && cast send $RECIPIENT \
  --value $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

**ERC20 token:**

```bash
set -a && source $ENV_FILE && set +a && cast send $TOKEN_ADDRESS "transfer(address,uint256)" $RECIPIENT $AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Step S.6: Result

```
Sent!

  TX Hash:    {txHash}
  Status:     Confirmed
  Network:    {network}

  From:       {walletAddress}
  To:         {recipient}
  Amount:     {amount} {token}

  Explorer:   {PHAROS_EXPLORER}/tx/{txHash}
```

## Phase 0: Dependency Check

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

The skill requires `helpers.py` for V3 quote math and mixSwap calldata encoding. It MUST be in the same directory as SKILL.md.

```bash
HELPERS_PATH="$(dirname "$0")/helpers.py"
# Or determine from skill installation directory:
# Claude Code: ~/.claude/skills/pharos-dex-swap-skill/helpers.py
# OpenClaw: ~/.openclaw/skills/pharos-dex-swap-skill/helpers.py

[ -f "$HELPERS_PATH" ] && echo "helpers.py found" || echo "helpers.py NOT found"
```

If not found → the skill is installed incorrectly. The user must ensure `helpers.py` is in the same folder as `SKILL.md`.

### Step 0.3: Check Dependencies

Run:

```bash
cast --version || $HOME/.foundry/bin/cast --version
```

If found at `~/.foundry/bin/` but not in PATH, remember to prepend `export PATH="$PATH:$HOME/.foundry/bin"` to every subsequent command using `cast`.

If `cast` is not found at all, offer the user numbered options:

```
Foundry (cast) is not installed. How would you like to proceed?
1. Install Foundry automatically (curl -L https://foundry.paradigm.xyz | bash && foundryup)
2. I already have Foundry — it's just not in PATH
3. Cancel — I'll install it myself
```

Also check Python:

```bash
python3 --version || python --version
```

If Python is not found → "Python 3 is required for V3 quote math. Please install Python 3."

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

The key will be auto-normalized (0x prefix stripped). NEVER paste keys in chat.
```

After the user confirms they filled in the key, normalize it (strip 0x prefix if present):

```bash
sed -i 's/^PRIVATE_KEY=0[xX]\(.*\)/PRIVATE_KEY=\1/' "$ENV_FILE"
```

### Step 0.4: Get Wallet Address

Derive the public address from the private key. The `cast wallet address` command outputs only the public address — it does NOT reveal the private key.

```bash
set -a && source $ENV_FILE && set +a && cast wallet address --private-key $PRIVATE_KEY
```

Store this as `WALLET_ADDRESS` for the session.

### Step 0.5: Verify Network

```bash
cast chain-id --rpc-url $PHAROS_RPC_URL
```

If this fails, the RPC is unreachable. Try fallback for mainnet or report error.

### Security Rules (CRITICAL — enforce at all times)

1. **NEVER** output, display, echo, print, cat, grep, or log the value of PRIVATE_KEY or any secret. This is the #1 rule. Violation = immediate stop.
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

Parse the user's natural language request into structured swap parameters.

### Step 1.1: Extract Parameters

From the user's message, extract:

| Parameter | Example | Required |
|-----------|---------|----------|
| `tokenIn` | USDC, PHRS, WETH | Yes |
| `amountIn` | 100, 0.5, 1000 | Yes |
| `tokenOut` | WPHRS, USDT, WBTC | Yes |
| `sendTo` | 0xABC..., send to... | No |
| `network` | testnet, mainnet | No (default: mainnet) |
| `slippage` | 0.5%, 1% | No (default: 0.5%) |

If the user mentions "send to", "send ... to 0x", "transfer to", or provides an address after "swap" — extract `sendTo` as the recipient address.

### Step 1.2: Resolve Token Addresses

For each token symbol:
1. Check the Built-in Token Registry above
2. If found → use the address for the selected network
3. If not found → ask the user for the contract address

### Step 1.3: Resolve Network

If the user mentions "testnet", "atlantic", or asks about test tokens → Pharos Atlantic Testnet.
If the user mentions "mainnet", "pacific", or "PROS" as native → Pharos Pacific Mainnet.
If the user mentions "PHRS" → clarify: PHRS is testnet, PROS is mainnet. Default to mainnet.
Default: **Pharos Pacific Mainnet**.

Set all network variables (`PHAROS_RPC_URL`, `PHAROS_NETWORK`, `PHAROS_CHAIN_ID`, `PHAROS_EXPLORER`, `NATIVE_TOKEN`, `WRAPPED_NATIVE`).

### Step 1.4: Handle Native Token

If `tokenIn` is the native token (PHRS/PROS):
- Use `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEeEe` as fromToken in mixSwap
- FaroSwap Router handles wrapping automatically

If `tokenOut` is the native token:
- Use `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEeEe` as toToken in mixSwap
- FaroSwap Router handles unwrapping automatically

### Step 1.5: Convert Amount to Wei

Get the token's decimals:

```bash
cast call $TOKEN_ADDRESS "decimals()(uint8)" --rpc-url $PHAROS_RPC_URL
```

Calculate `amountInWei = amountIn * 10^decimals`. Use:

```bash
python3 -c "print(int($AMOUNT * 10**$DECIMALS))"
```

## Phase 2: Pool Discovery via V3 Factory

**Target: complete in under 3 seconds.**

### Step 2.1: Determine Token Pair for Factory Query

For Factory `getPool()`, use the **wrapped** token addresses (not native `0xEeeee...`):
- If tokenIn is native → use WPROS/WPHRS address
- If tokenOut is native → use WPROS/WPHRS address

Store both addresses as `TOKEN_A` and `TOKEN_B`.

### Step 2.2: Query Factory for All Fee Tiers

```bash
FACTORY="0x2c90CcB0b989afA2433F499698451a25744A552b"
RPC="$PHAROS_RPC_URL"

for FEE in 100 500 3000 10000; do
  POOL=$(cast call $FACTORY "getPool(address,address,uint24)(address)" $TOKEN_A $TOKEN_B $FEE --rpc-url $RPC 2>/dev/null)
  if [ -n "$POOL" ] && [ "$POOL" != "0x0000000000000000000000000000000000000000" ]; then
    echo "FEE=$FEE POOL=$POOL"
  fi
done
```

Each successful call returns the V3 pool address for that fee tier.

### Step 2.3: Check Liquidity for Each Pool

For each discovered pool:

```bash
LIQ=$(cast call $POOL "liquidity()(uint128)" --rpc-url $RPC)
echo "POOL=$POOL LIQUIDITY=$LIQ"
```

- If `liquidity == 0` → **skip** (no active liquidity in current tick)
- If `liquidity > 0` → **valid candidate**, add to list

### Step 2.4: Read Pool State for Quoting

For each valid pool, read `slot0()` and `token0()`:

```bash
# Get sqrtPriceX96 and tick
SLOT0=$(cast call $POOL "slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)" --rpc-url $RPC)
SQRT_PRICE=$(echo $SLOT0 | awk '{print $1}')

# Get token0 to determine direction
TOKEN0=$(cast call $POOL "token0()(address)" --rpc-url $RPC)
```

Store for each pool: `{pool_address, sqrtPriceX96, liquidity, token0, fee}`

### Step 2.5: No Pools Found

If no pools with liquidity exist:

```
No V3 pools with liquidity found for {tokenIn} -> {tokenOut} on Pharos {network}.

Checked fee tiers: 0.01%, 0.05%, 0.3%, 1%

Suggestions:
1. Try a different pair (e.g., WPROS <-> USDC)
2. Check available pairs on faroswap.xyz
3. Try again later — liquidity may be added
```

**Do NOT attempt the swap.** Stop and inform the user.

## Phase 3: Quote and Safety Check

Quote all valid pools using Python V3 math, apply safety filters, pick the best.

### Step 3.1: Determine Swap Direction

For each pool, compare `token0` with the input token address:

```bash
# zeroForOne = true if selling token0 (token0 == wrapped tokenIn)
# zeroForOne = false if selling token1 (token1 == wrapped tokenIn)
```

If `token0 == TOKEN_A` (where TOKEN_A is the wrapped input token) → `zeroForOne = true`
If `token0 != TOKEN_A` → `zeroForOne = false`

### Step 3.2: Compute Quotes with Python Helper

For each pool, run the quote helper:

```bash
RESULT=$(python3 helpers.py quote \
  --sqrt-price $SQRT_PRICE_X96 \
  --liquidity $LIQUIDITY \
  --amount $AMOUNT_IN_WEI \
  --decimals-in $DECIMALS_IN \
  --decimals-out $DECIMALS_OUT \
  --zero-for-one $ZERO_FOR_ONE)
```

The helper returns JSON: `{"amountOut": N, "priceImpactBps": M}`

### Step 3.3: Liquidity Safety Check

**Rule: If `amountInWei` > 10% of the pool's active liquidity → SKIP this pool.**

Since V3 liquidity is in L² units (not directly comparable to token amounts), use the quote result as proxy:
- If `priceImpactBps > 3000` (30%) → likely exceeding safe pool capacity, skip

### Step 3.4: Apply Price Impact Threshold

**Default threshold: 3% (300 basis points).**

- `priceImpactBps <= 300` → pool is VALID
- `priceImpactBps > 300` → pool is REJECTED

### Step 3.5: Sort and Select Best Pool

Among all valid pools, sort by `amountOut` descending (highest output = best rate).

Select the pool with the best rate.

### Step 3.6: All Pools Rejected

If all pools are rejected (zero liquidity, price impact too high):

```
Swap rejected: no pools with acceptable conditions for {tokenIn} -> {tokenOut}.

{For each pool, show why:}
  Pool {address} (fee={fee}%):
    Liquidity: {liquidity}
    Price impact: {impact}% — EXCEEDS 3% threshold
    Quote: would receive {amount} {tokenOut}

Suggestions:
1. Reduce swap amount (currently {amountIn} {tokenIn})
2. Choose a different token pair
3. Accept higher price impact (risky)
```

**Do NOT proceed. Wait for user response.**

## Phase 4: Auto-Execute Decision

**CRITICAL BEHAVIOR CHANGE from v1.x:** The agent does NOT ask for confirmation when all safety checks pass. It proceeds directly to execution.

### Step 4.1: Safety Gate (Automatic)

All of these must be true to auto-execute:
- At least one pool with valid quote exists (Phase 3 passed)
- Price impact ≤ 3% (300 bps)
- Wallet has sufficient balance for the swap
- Slippage is within default bounds (0.5%)

If ALL pass → **skip to Phase 5 immediately**. Do NOT ask "Confirm swap?".

If ANY fails → **stop and inform the user with specific reason and options**.

### Step 4.2: Balance Check (Pre-Execution)

```bash
set -a && source $ENV_FILE && set +a && cast call $TOKEN_IN_ADDRESS "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

For native token input:

```bash
set -a && source $ENV_FILE && set +a && cast balance $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

If balance < amountIn:

```
Insufficient balance.

  Token:    {tokenIn}
  Required: {amountIn}
  Balance:  {balance}

1. Swap {balance} {tokenIn} instead (max available)
2. Cancel
```

**Stop. Wait for user response.**

### Step 4.3: Price Impact Override (Only if > 3%)

If price impact exceeds 3% but the user still wants to proceed:

```
WARNING: Price impact is {impact}% — above the safe 3% threshold.

What this means:
- You are trading a large amount relative to pool liquidity
- The exchange rate is {impact}% worse than the ideal price
- You lose approximately ~{lossAmount} {tokenOut} on this trade

Example:
  You send:     {amountIn} {tokenIn}
  You receive:  {quoteHuman} {tokenOut}
  Fair value:   {fairValue} {tokenOut}
  Difference:   -{lossAmount} {tokenOut}

1. Accept {impact}% impact — swap anyway
2. Reduce swap amount (recommended)
3. Cancel
```

**Do NOT proceed unless the user explicitly selects option 1.**

### Step 4.4: Show Status During Execution

While executing (Phase 5), display progress to the user:

```
Swapping {amountIn} {tokenIn} -> {amountOut} {tokenOut}...

  Pool: {poolAddress} (fee: {fee}%)
  Rate: 1 {tokenIn} = {rate} {tokenOut}
  Price impact: {impact}%
  Slippage tolerance: {slippage}%
```

## Phase 5: Execute Swap

### Step 5.1: Compute Slippage-Protected Min Return

```bash
# minReturn = quote * (100 - slippage) / 100
MIN_RETURN=$(python3 -c "print(int($QUOTE * (100 - $SLIPPAGE) / 100))")
```

Default slippage: 0.5%

### Step 5.2: Compute Deadline

```bash
DEADLINE=$(($(date +%s) + 600))
```

### Step 5.3: Determine Direction

```bash
# direction = 0 if fromToken address < toToken address (lexicographic)
# direction = 1 if fromToken address > toToken address
# For native token: use 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEeEe
python3 -c "
a = '$FROM_TOKEN'.lower()
b = '$TO_TOKEN'.lower()
print(0 if a < b else 1)
"
```

### Step 5.4: Token Approval (if not native token)

For ERC20 tokenIn, approve the DODO Approve Proxy:

```bash
APPROVE_PROXY="0x2aFc65f51B8afd1dB9618643F89f0b135EaAeEAa"

# Check current allowance
set -a && source $ENV_FILE && set +a && cast call $TOKEN_IN "allowance(address,address)(uint256)" $WALLET_ADDRESS $APPROVE_PROXY --rpc-url $PHAROS_RPC_URL
```

If `allowance < amountInWei` → approve exact amount:

```bash
set -a && source $ENV_FILE && set +a && cast send $TOKEN_IN "approve(address,uint256)" $APPROVE_PROXY $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

**CRITICAL: approve exact amount only. NEVER type(uint256).max.**

If `tokenIn` is native (`0xEeeee...`) → skip approval. The router handles native tokens via msg.value.

### Step 5.5: Encode mixSwap Calldata

Use the Python helper to encode:

```bash
CALLDATA=$(python3 helpers.py encode \
  --from-token $FROM_TOKEN \
  --to-token $TO_TOKEN \
  --amount $AMOUNT_IN_WEI \
  --min-return $MIN_RETURN \
  --expected $QUOTE \
  --pool $POOL_ADDRESS \
  --fee $FEE \
  --adapter 0x4fd44181839d24e7c8f4d1b9288379109ec25fae \
  --router 0xA5cA5Fbe34e444F366B373170541ec6902b0F75c \
  --direction $DIRECTION \
  --deadline $DEADLINE)
```

### Step 5.6: Execute the Swap

```bash
ROUTER="0xA5cA5Fbe34e444F366B373170541ec6902b0F75c"

set -a && source $ENV_FILE && set +a && cast send $ROUTER "$CALLDATA" \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

If `tokenIn` is native → add `--value $AMOUNT_IN_WEI`:

```bash
set -a && source $ENV_FILE && set +a && cast send $ROUTER "$CALLDATA" \
  --value $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Step 5.7: Handle Failure

If the swap transaction reverts:

```
Swap failed — transaction reverted.

Possible reasons:
- Price moved beyond slippage tolerance (try again or increase slippage)
- Pool liquidity changed during the swap
- Approval expired or was insufficient

The swap amount is still in your wallet. Nothing was lost.

1. Try again (get a fresh quote)
2. Increase slippage and retry
3. Cancel
```

## Phase 5.8: Send Swapped Tokens (if requested)

If the user specified a recipient address in their request (e.g., "swap 10 PROS to USDC and send to 0x..."), execute a transfer of the received tokens to that address after the swap completes.

**Extract recipient address** from the user's original message during Phase 1. Store it as `SEND_TO_ADDRESS`.

### Validate Recipient

```bash
cast --to-checksum-address $SEND_TO_ADDRESS
```

If invalid → ask user to provide a valid address.

### Send ERC20 Tokens

```bash
set -a && source $ENV_FILE && set +a && cast send $TOKEN_OUT "transfer(address,uint256)" $SEND_TO_ADDRESS $RECEIVED_AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Send Native Token (if tokenOut was native)

```bash
set -a && source $ENV_FILE && set +a && cast send $SEND_TO_ADDRESS \
  --value $RECEIVED_AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

## Phase 6: Result

On successful swap, present the result:

```
Swap complete!

  TX Hash:    {txHash}
  Status:     Confirmed
  Network:    {network}

  Sent:       {amountIn} {tokenIn}
  Received:   {amountOut} {tokenOut}
  Rate:       1 {tokenIn} = {rate} {tokenOut}
  Pool:       {poolAddress} ({fee}% fee tier)
  Price impact: {impact}%

  Explorer:   {PHAROS_EXPLORER}/tx/{txHash}
```

If tokens were sent to a recipient after the swap (Phase 5.8), append:

```
  Sent to:    {SEND_TO_ADDRESS}
  Send TX:    {sendTxHash}
  Send Explorer: {PHAROS_EXPLORER}/tx/{sendTxHash}
```

Update `state.json` with the swap details:

```json
{
  "lastSwap": {
    "txHash": "0x...",
    "tokenIn": "USDC",
    "tokenOut": "WPROS",
    "amountIn": "100000000",
    "amountOut": "98500000000000000000",
    "pool": "0x...",
    "fee": 100,
    "network": "pharos-mainnet",
    "timestamp": "2026-05-28T12:00:00Z"
  }
}
```

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
