---
name: pharos-dex-swap-skill
description: Pharos DEX token swap, wallet balance check, and token transfer — auto-discovers DODO-based pools (FaroSwap, Zenith, custom), checks liquidity and price impact, protects against bad trades with slippage guard and exact-amount-only approvals, executes swap via cast, queries all token balances, sends native and ERC20 tokens to any address.
version: 1.0.0
frameworks:
  - openclaw
  - claude-code
  - codex
tags:
  - dex
  - swap
  - trade
  - faroswap
  - dodo
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

Swap tokens on Pharos through FaroSwap and other DODO-based DEX pools. The skill auto-discovers all available pools for a token pair, checks liquidity, warns about price impact, and executes swaps safely with exact-amount approvals and slippage protection. Also supports wallet balance checks and direct token transfers (native and ERC20).

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

If the user does not specify a network, default to **Pharos Atlantic Testnet**.

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

1. **Native tokens** — `PHRS`, `PROS`, `ETH` (as native) → the native gas token. Address is `0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeEEEeeEEEeE`. These must be wrapped before swapping through DEX pools.
2. **Wrapped native** — `WPHRS`, `WPROS` → use the address from the registry above.
3. **Known tokens** — `USDC`, `USDT`, `WETH`, `WBTC`, `LINK` → use the address from the registry for the selected network.
4. **Custom tokens** — if the symbol is not in the registry, ask the user for the contract address. Verify it is a valid ERC20 by calling `name()`, `symbol()`, `decimals()`.

## Capabilities

- **Token Swap** — Swap any ERC20 token for another through DODO-based AMM pools on Pharos.
- **Pool Auto-Discovery** — Automatically find all pools for a token pair by scanning on-chain data. Supports FaroSwap, Zenith, and custom DODO-based pools.
- **Liquidity Safety Check** — Verify pool reserves before quoting. Skip empty or low-liquidity pools. Reject swaps that exceed 10% of pool reserves.
- **Price Impact Guard** — Hard threshold (default 3%) that blocks swaps with excessive price impact. User can override only after reading a clear risk explanation.
- **Exact-Amount Approval** — Approve tokens for the exact swap amount only. NEVER approve unlimited spending.
- **Slippage Protection** — Enforce minimum output amount. Transaction reverts if price moves beyond tolerance (default 0.5%).
- **Native Token Handling** — Automatically wrap PHRS/PROS before swapping, unwrap after if needed.
- **Multi-Pool Comparison** — When multiple pools exist for a pair, quote all of them and pick the best rate.
- **Wallet Balance Check** — Query native token balance and all known ERC20 token balances. Report only non-zero holdings in human-readable format.
- **Send After Swap** — Optionally send swapped tokens to a specified address after the swap completes.

## DODO V2 Function Reference

FaroSwap and Zenith are DODO V2 forks. The agent uses these function signatures to interact with pools. All calls use `cast`.

### Pool Functions (DODODvm / FPool)

```
# Read pool token addresses
_BASE_TOKEN_()(address)
_QUOTE_TOKEN_()(address)

# Read pool reserves
_BASE_RESERVE_()(uint256)
_QUOTE_RESERVE_()(uint256)

# Get swap quote (view — no gas cost)
# NOTE: Some DODO versions include the trader address, others do not.
# If the version with trader fails, try without it.
querySellBase(address trader, uint256 payBaseAmount)(uint256 receiveQuoteAmount)
querySellBase(uint256 payBaseAmount)(uint256 receiveQuoteAmount)
querySellQuote(address trader, uint256 payQuoteAmount)(uint256 receiveBaseAmount)
querySellQuote(uint256 payQuoteAmount)(uint256 receiveBaseAmount)

# Execute swap
sellBase(address trader, uint256 payBaseAmount)(uint256 receiveQuoteAmount)
sellQuote(address trader, uint256 payQuoteAmount)(uint256 receiveBaseAmount)
```

### Route Proxy Functions

```
# Swap through router with slippage protection
mixSwap(address fromToken, address toToken, uint256 fromTokenAmount, uint256 minReturnAmount, address[] pools, uint256 deadline)(uint256 receiveAmount)
```

### Factory Functions

```
# Get pool for a token pair
getDODOPool(address baseToken, address quoteToken)(address pool)

# Get pool count (if supported by the factory version)
getDODOPoolCount(address baseToken, address quoteToken)(uint256 count)

# Get pool by index (if supported by the factory version)
getDODOPoolByIndex(address baseToken, address quoteToken, uint256 index)(address pool)
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

Same rules as Phase 1.3 — detect from user's message or default to testnet.

### Step B.2: Check Native Token Balance

```bash
set -a && source .env && set +a && cast balance $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

Convert from wei to human-readable:

```bash
cast from-wei $BALANCE
```

### Step B.3: Check ERC20 Token Balances

For each token in the Built-in Token Registry for the selected network:

```bash
set -a && source .env && set +a && cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

Convert from raw units to human-readable using the token's decimals:

```bash
# Divide by 10^decimals (use bc or cast)
echo "scale=6; $RAW_BALANCE / (10 ^ $DECIMALS)" | bc
```

### Step B.4: Report Results

Show only tokens with non-zero balance. Format:

```
Wallet: {walletAddress} on {network}

  {NATIVE_TOKEN}:  {balance} (≈ ${usdValue} if known)
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
| `network` | testnet, mainnet | No (default: testnet) |

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
set -a && source .env && set +a && cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL

# For native token
set -a && source .env && set +a && cast balance $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
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
set -a && source .env && set +a && cast send $RECIPIENT \
  --value $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

**ERC20 token:**

```bash
set -a && source .env && set +a && cast send $TOKEN_ADDRESS "transfer(address,uint256)" $RECIPIENT $AMOUNT \
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

1. Check if `.env` exists in the project root directory.
2. If `.env` does NOT exist, create it with:

```
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
```

3. Ensure `.env` is in `.gitignore`. If `.gitignore` exists but has no `.env` entry, append it. If `.gitignore` does not exist, create it with `.env` on the first line.

### Step 0.2: Check Dependencies

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

### Step 0.3: Verify Private Key

```bash
set -a && source .env && set +a && echo "PRIVATE_KEY set: $([ -n \"$PRIVATE_KEY\" ] && echo 'yes' || echo 'no')"
```

If not set, guide the user:

```
Please open the .env file and add your private key:
  File: {absolute_path_to_.env}

Set: PRIVATE_KEY=your_key_here (with or without 0x prefix)

The key will be auto-normalized (0x prefix stripped). NEVER paste keys in chat.
```

After the user confirms they filled in the key, normalize it (strip 0x prefix if present):

```bash
sed -i 's/^PRIVATE_KEY=0[xX]\(.*\)/PRIVATE_KEY=\1/' .env
```

### Step 0.4: Get Wallet Address

```bash
set -a && source .env && set +a && cast wallet address --private-key $PRIVATE_KEY
```

Store this as `WALLET_ADDRESS` for the session.

### Step 0.5: Verify Network

```bash
cast chain-id --rpc-url $PHAROS_RPC_URL
```

If this fails, the RPC is unreachable. Try fallback for mainnet or report error.

### Security Rules (CRITICAL — enforce at all times)

1. **NEVER** ask the user to paste private keys or secrets in chat
2. **NEVER** display or log the value of PRIVATE_KEY
3. **ALWAYS** show the full absolute path to the `.env` file
4. **NEVER** approve unlimited token spending — exact swap amount only
5. If the user accidentally pastes a secret in chat — warn immediately, suggest rotating the key

## Shell State Note (CRITICAL)

Shell state does NOT persist between Bash tool calls. EVERY command that uses env vars MUST start with:

```bash
set -a && source /absolute/path/to/.env && set +a && ...rest of command...
```

Use the **absolute path** to `.env` — relative `source .env` fails if the working directory changes.

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
| `network` | testnet, mainnet | No (default: testnet) |
| `slippage` | 0.5%, 1% | No (default: 0.5%) |

If the user mentions "send to", "send ... to 0x", "transfer to", or provides an address after "swap" — extract `sendTo` as the recipient address. The swap will execute normally, then the received tokens will be sent to this address.

### Step 1.2: Resolve Token Addresses

For each token symbol:
1. Check the Built-in Token Registry above
2. If found → use the address for the selected network
3. If not found → ask the user for the contract address

### Step 1.3: Resolve Network

If the user mentions "testnet", "atlantic", or "PHRS" as native → Pharos Atlantic Testnet.
If the user mentions "mainnet", "pacific", or "PROS" as native → Pharos Pacific Mainnet.
Default: Pharos Atlantic Testnet.

Set all network variables (`PHAROS_RPC_URL`, `PHAROS_NETWORK`, `PHAROS_CHAIN_ID`, `PHAROS_EXPLORER`, `NATIVE_TOKEN`, `WRAPPED_NATIVE`).

### Step 1.4: Handle Native Token

If `tokenIn` is the native token (PHRS/PROS):
- The actual swap will use the wrapped version (WPHRS/WPROS)
- Agent will auto-wrap before swapping
- Note this for the user: "PHRS will be wrapped to WPHRS before swapping"

If `tokenOut` is the native token:
- The swap will produce the wrapped version
- Agent will auto-unwrap after swapping
- Note this for the user: "You'll receive WPHRS first, then it will be unwrapped to PHRS"

### Step 1.5: Convert Amount to Wei

Get the token's decimals:

```bash
cast call $TOKEN_ADDRESS "decimals()(uint8)" --rpc-url $PHAROS_RPC_URL
```

Calculate `amountInWei = amountIn * 10^decimals`. For example:
- 100 USDC (6 decimals) → `100000000` (100 * 10^6)
- 0.5 WETH (18 decimals) → `500000000000000000` (0.5 * 10^18)

Use `cast` to convert:

```bash
# For 18-decimal tokens
cast to-unit $AMOUNT eth

# For arbitrary decimals — compute directly
python3 -c "print(int($AMOUNT * 10**$DECIMALS))"
```

Or compute programmatically.

## Phase 2: Pool Discovery

Find ALL DODO-based pools for the token pair on the selected network.

### Step 2.1: Check Cache

```bash
# Check if pools are cached in state.json
cat state.json 2>/dev/null | jq -r ".pools[\"$TOKEN_SYMBOL_PAIR\"] // empty"
```

If cached pools exist, skip to Step 2.4 to verify they are still active (pools can be drained between sessions).

If no cache or cache is empty, proceed with discovery.

### Step 2.2: Scan for Pool Contracts

Scan recent Transfer events on the tokens to find interacting contracts. Use the wrapped native token (WPHRS/WPROS) if one of the tokens is native.

```bash
BLOCK=$(cast block-number --rpc-url $PHAROS_RPC_URL)
# Scan last 10000 blocks (enough to find active pools, fast to query)
FROM_BLOCK=$((BLOCK - 10000))

# Scan Transfer events on tokenIn
cast logs --address $TOKEN_IN --from-block $FROM_BLOCK --to-block $BLOCK \
  "Transfer(address,address,uint256)" --rpc-url $PHAROS_RPC_URL
```

If this returns too many results or times out, reduce the range to 5000 or 2000 blocks. If no Transfer events found, try scanning `tokenOut` instead.

Parse the output to extract unique `from` and `to` addresses. For each unique address:
1. Check if it is a contract (has bytecode):

```bash
cast code $ADDRESS --rpc-url $PHAROS_RPC_URL
# Non-empty "0x" output = contract
```

2. For each contract, try calling DODO pool functions:

```bash
cast call $CONTRACT "_BASE_TOKEN_()(address)" --rpc-url $PHAROS_RPC_URL 2>/dev/null
cast call $CONTRACT "_QUOTE_TOKEN_()(address)" --rpc-url $PHAROS_RPC_URL 2>/dev/null
```

3. If BOTH calls succeed and return valid addresses → this is a DODO pool.

### Step 2.3: Filter Pools by Token Pair

For each discovered DODO pool:
1. Get `_BASE_TOKEN_()` and `_QUOTE_TOKEN_()` addresses
2. Check if the pool matches our pair (in either direction):
   - (baseToken == tokenIn AND quoteToken == tokenOut) OR
   - (baseToken == tokenOut AND quoteToken == tokenIn)
3. If it matches → add to the pool list

Also try the DODOZoo factory approach if a factory address is discovered:
```bash
cast call $FACTORY "getDODOPool(address,address)(address)" $TOKEN_IN $TOKEN_OUT --rpc-url $PHAROS_RPC_URL 2>/dev/null
```

### Step 2.4: Verify Pools and Check Reserves

For each pool in the list:

```bash
# Get reserves
BASE_RESERVE=$(cast call $POOL "_BASE_RESERVE_()(uint256)" --rpc-url $PHAROS_RPC_URL)
QUOTE_RESERVE=$(cast call $POOL "_QUOTE_RESERVE_()(uint256)" --rpc-url $PHAROS_RPC_URL)
```

- If both reserves are 0 → **remove pool** (dead pool)
- If one reserve is 0 → **remove pool** (one-sided, unusable for swaps)
- Keep pools with non-zero reserves on both sides

### Step 2.5: Cache Results

Save discovered pools to `state.json`:

```json
{
  "network": "pharos-testnet",
  "wallet": "0x...",
  "pools": {
    "WPHRS-USDC": [
      {
        "address": "0x...",
        "baseToken": "0x...",
        "quoteToken": "0x...",
        "discoveredAt": "2026-05-27T12:00:00Z"
      }
    ]
  },
  "lastSwap": null
}
```

### Step 2.6: No Pools Found

If after all discovery steps no valid pools exist for the pair:

```
No pools found for {tokenIn} → {tokenOut} on Pharos {network}.

Possible reasons:
- This trading pair does not exist yet on FaroSwap or other DEXes
- All pools for this pair have been drained

Available pairs (from discovered pools):
  - WPHRS / USDC (pool: 0x...)
  - WPHRS / USDT (pool: 0x...)

Would you like to swap a different pair?
```

**Do NOT attempt the swap.** Stop and inform the user.

## Phase 3: Quote and Safety Check

For each valid pool, get a quote and apply safety filters.

### Step 3.1: Get Quotes

Determine the swap direction for each pool:
- If `tokenIn == baseToken` → use `querySellBase`
- If `tokenIn == quoteToken` → use `querySellQuote`

```bash
# Example: tokenIn is the base token
QUOTE=$(cast call $POOL "querySellBase(address,uint256)(uint256)" $WALLET_ADDRESS $AMOUNT_IN_WEI --rpc-url $PHAROS_RPC_URL)

# Example: tokenIn is the quote token
QUOTE=$(cast call $POOL "querySellQuote(address,uint256)(uint256)" $WALLET_ADDRESS $AMOUNT_IN_WEI --rpc-url $PHAROS_RPC_URL)
```

If the call reverts → skip this pool (swap not possible).

### Step 3.2: Reserve Safety Check

For each pool with a valid quote:

```bash
BASE_RESERVE=$(cast call $POOL "_BASE_RESERVE_()(uint256)" --rpc-url $PHAROS_RPC_URL)
QUOTE_RESERVE=$(cast call $POOL "_QUOTE_RESERVE_()(uint256)" --rpc-url $PHAROS_RPC_URL)
```

**Rule: If `amountInWei` > 10% of the input token's reserve → SKIP this pool.**

```
Swap amount ({amountIn}) is {percent}% of the pool's reserve ({reserve}).
Maximum allowed: 10% of pool reserves.
This pool is skipped to protect against extreme price impact.
```

### Step 3.3: Calculate Price Impact

```
midPrice = reserveOut / reserveIn
executedPrice = quote / amountIn
priceImpact = (midPrice - executedPrice) / midPrice * 100
```

If `priceImpact < 0` (rare, means better than mid price) → set to 0.

### Step 3.4: Apply Price Impact Threshold

**Default threshold: 3%.**

- `priceImpact <= 3%` → pool is VALID, add to candidates
- `priceImpact > 3%` → pool is REJECTED

### Step 3.5: Sort and Select Best Pool

Among all valid pools, sort by `quote` descending (highest output = best rate).

Select the pool with the best rate.

### Step 3.6: All Pools Rejected

If all pools are rejected (reserves too low, price impact too high, or quotes failed):

```
Swap rejected: no pools with acceptable liquidity for {tokenIn} → {tokenOut}.

Reason:
- Pools found: {count}
- Pools with sufficient reserves: {count}
- Pools within price impact threshold (3%): 0

{For each rejected pool, show why:}
  Pool {address}:
    Reserves: {base} {tokenIn} / {quote} {tokenOut}
    Price impact: {impact}% — EXCEEDS 3% threshold
    Quote: would receive {amount} {tokenOut}

Suggestions:
1. Reduce swap amount (currently {amountIn} {tokenIn})
2. Choose a different token pair
3. Increase price impact threshold (risky — see details below)
```

## Phase 4: Confirm with User

Present the best quote to the user for confirmation.

### Step 4.1: Normal Confirmation (price impact within threshold)

```
Swap quote:

  Send:      {amountIn} {tokenIn}
  Receive:   ~{quoteHuman} {tokenOut}
  Rate:      1 {tokenIn} = {rate} {tokenOut}
  Pool:      {poolAddress} (reserves: {resIn} {tokenIn} / {resOut} {tokenOut})
  Price impact: {impact}%
  Slippage:  {slippage}%
  Network:   {network}
  {if sendTo:} Send to:  {sendToAddress}

Confirm this swap{if sendTo: + send}?
1. Yes, swap now
2. Cancel
```

### Step 4.2: Override Option (only shown after rejection)

If the user asks to proceed despite price impact > 3%:

```
WARNING: Price impact is {impact}% — above the safe 3% threshold.

What this means:
- You are trading a large amount relative to pool liquidity
- The exchange rate is {impact}% worse than the ideal market price
- On a {amountIn} {tokenIn} swap, you lose approximately ~{lossAmount} {tokenOut}

Example with {impact}% price impact:
  You send:     {amountIn} {tokenIn}
  You receive:  {quoteHuman} {tokenOut}
  Fair value:   {fairValue} {tokenOut}
  Difference:   -{lossAmount} {tokenOut}

Risks of high price impact:
- Permanent loss of value on this trade
- The larger the swap relative to pool size, the worse the rate
- No recovery mechanism — the loss is immediate

Are you sure?
1. Yes, I accept the {impact}% price impact — swap anyway
2. No, cancel the swap
3. Reduce the swap amount (recommended)
```

**The agent MUST NOT proceed with the swap unless the user explicitly selects option 1.**

### Step 4.3: Configure Slippage

Default slippage: **0.5%**. The user can request a different value.

```bash
minAmountOut=$(cast --to-unit $(echo "$QUOTE * (100 - $SLIPPAGE) / 100" | bc) wei)
```

Or calculate: `minAmountOut = quote * (100 - slippage) / 100`

## Phase 5: Execute Swap

### Step 5.1: Check Balance

```bash
set -a && source .env && set +a && cast call $TOKEN_IN "balanceOf(address)(uint256)" $WALLET_ADDRESS --rpc-url $PHAROS_RPC_URL
```

If balance < amountIn:

```
Insufficient balance.

  Token:    {tokenIn}
  Required: {amountIn}
  Balance:  {balance}

Options:
1. Swap {balance} {tokenIn} instead (max available)
2. Cancel
```

### Step 5.2: Wrap Native Token (if needed)

If `tokenIn` is the native token (PHRS/PROS):

```bash
set -a && source .env && set +a && cast send $WRAPPED_NATIVE "deposit()" \
  --value $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

Wait for confirmation. Then set `tokenIn` to the wrapped version for subsequent steps.

### Step 5.3: Check and Set Allowance

```bash
set -a && source .env && set +a && cast call $TOKEN_IN "allowance(address,address)(uint256)" $WALLET_ADDRESS $POOL_ADDRESS --rpc-url $PHAROS_RPC_URL
```

If `allowance >= amountInWei` → skip approve, go to Step 5.4.

If `allowance < amountInWei` → approve the **EXACT** swap amount:

```bash
set -a && source .env && set +a && cast send $TOKEN_IN "approve(address,uint256)" $POOL_ADDRESS $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

**CRITICAL SAFETY RULE:** The approve amount MUST be `amountInWei` — the exact swap amount. NEVER use `type(uint256).max` or any unlimited value. If the current allowance is > 0 but < amountIn, first reset to 0, then approve the exact amount (some ERC20 implementations require this).

Wait for the approve transaction to be confirmed before proceeding.

### Step 5.4: Execute the Swap

Determine swap direction:
- If tokenIn is the base token → `sellBase`
- If tokenIn is the quote token → `sellQuote`

```bash
# If tokenIn is base token:
set -a && source .env && set +a && cast send $POOL_ADDRESS "sellBase(address,uint256)(uint256)" \
  $WALLET_ADDRESS $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy

# If tokenIn is quote token:
set -a && source .env && set +a && cast send $POOL_ADDRESS "sellQuote(address,uint256)(uint256)" \
  $WALLET_ADDRESS $AMOUNT_IN_WEI \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

If the DODORouteProxy is discovered, prefer it for slippage protection:

```bash
DEADLINE=$(($(date +%s) + 600))  # 10 minutes from now

set -a && source .env && set +a && cast send $ROUTE_PROXY "mixSwap(address,address,uint256,uint256,address[],uint256)" \
  $TOKEN_IN $TOKEN_OUT $AMOUNT_IN_WEI $MIN_AMOUNT_OUT "[$POOL_ADDRESS]" $DEADLINE \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Step 5.5: Unwrap Native Token (if needed)

If `tokenOut` is the native token and the swap produced the wrapped version:

```bash
set -a && source .env && set +a && cast send $WRAPPED_NATIVE "withdraw(uint256)" $RECEIVED_AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Step 5.6: Handle Failure

If the swap transaction reverts:

```
Swap failed — transaction reverted.

Possible reasons:
- Price moved beyond slippage tolerance (try again or increase slippage)
- Pool reserves changed during the swap
- Approval expired or was insufficient

The swap amount is still in your wallet. Nothing was lost.
Would you like to:
1. Try again (get a fresh quote)
2. Increase slippage and retry
3. Cancel
```

## Phase 5.7: Send Swapped Tokens (if requested)

If the user specified a recipient address in their request (e.g., "swap 10 PROS to USDC and send to 0x..."), execute a transfer of the received tokens to that address after the swap completes.

**Extract recipient address** from the user's original message during Phase 1. Store it as `SEND_TO_ADDRESS`.

### Validate Recipient

```bash
# Verify address format
cast --to-checksum-address $SEND_TO_ADDRESS
```

If invalid → ask user to provide a valid address.

### Send ERC20 Tokens

```bash
set -a && source .env && set +a && cast send $TOKEN_OUT "transfer(address,uint256)" $SEND_TO_ADDRESS $RECEIVED_AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

### Send Native Token (if tokenOut was unwrapped)

```bash
set -a && source .env && set +a && cast send $SEND_TO_ADDRESS \
  --value $RECEIVED_AMOUNT \
  --rpc-url $PHAROS_RPC_URL \
  --private-key $PRIVATE_KEY \
  --legacy
```

Wait for the send transaction to be confirmed. Record the send tx hash.

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
  Pool:       {poolAddress}

  Explorer:   {PHAROS_EXPLORER}/tx/{txHash}
```

If tokens were sent to a recipient after the swap (Phase 5.7), append:

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
    "tokenOut": "WPHRS",
    "amountIn": "100000000",
    "amountOut": "98500000000000000000",
    "pool": "0x...",
    "network": "pharos-testnet",
    "timestamp": "2026-05-27T12:00:00Z"
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
| No pools found | The token pair may not be traded on any Pharos DEX. Suggest available pairs. |
| All pools have 0 reserves | No liquidity. Inform user, suggest waiting or using a different pair. |
| Quote reverts | Pool may be paused or broken. Skip it, try other pools. Try alternate function signature (with/without trader param). |
| Approve fails | Check that PRIVATE_KEY is correct and wallet has PHRS/PROS for gas. |
| Swap reverts | Price likely moved. Get a fresh quote and retry. |
| Send fails (transfer) | Check token balance and gas. Verify recipient address. |
| Insufficient gas | Wallet needs PHRS (testnet) or PROS (mainnet) for transaction fees. |
| `.env` not loading | Use absolute path: `source /full/path/to/.env` |
| DODO function not found | Try alternate signature — some pools use `querySellBase(uint256)` without trader address |

## Example Usage Prompts

### Swaps
1. **"Swap 100 USDC to WPHRS on Pharos"** — Standard swap
2. **"Trade 0.5 PHRS for USDC on Pharos testnet"** — Native token wrapping + swap
3. **"Convert all my USDT to WPHRS"** — Swap full balance
4. **"Swap 50 USDC to USDT on Pharos mainnet"** — Mainnet swap
5. **"Exchange 1000 WPHRS for WBTC"** — Large swap with impact check
6. **"What's the rate for 100 USDC to WPHRS?"** — Quote only, no execution

### Balance Check
7. **"How much money do I have on Pharos?"** — Balance check (all tokens)
8. **"Show my Pharos wallet balance"** — Balance check

### Send
9. **"Send 10 USDC to 0xABC..."** — Direct ERC20 transfer
10. **"Send 0.5 PROS to 0xABC... on mainnet"** — Direct native transfer
11. **"Transfer 100 WETH to 0xABC..."** — Direct ERC20 transfer

### Combined (Swap + Send)
12. **"Swap 10 PROS to USDC and send to 0xABC..."** — Swap + send to address
13. **"Convert 50 USDC to WPHRS and send to 0xABC..."** — Swap + send
