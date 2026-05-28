"""
FaroSwap V3 helpers for Pharos DEX Swap Skill.

Commands:
  python3 helpers.py quote  --sqrt-price X --liquidity Y --amount Z --decimals-in D --decimals-out D --zero-for-one [true|false]
  python3 helpers.py encode --from-token A --to-token A --amount N --min-return N --expected N --pool A --fee N --adapter A --router A --direction N --deadline N
  python3 helpers.py swap   --from TOKEN --to TOKEN --amount N [--network mainnet|testnet] [--rpc URL]
  python3 helpers.py balance [--network mainnet|testnet] [--rpc URL]
  python3 helpers.py send   --token TOKEN --amount N --to ADDRESS [--network mainnet|testnet] [--rpc URL]
"""
import sys
import os
import argparse
import json
import subprocess
import time

# Add foundry to PATH
_home = os.path.expanduser('~')
_foundry_bin = os.path.join(_home, '.foundry', 'bin')
if os.path.isdir(_foundry_bin):
    os.environ['PATH'] = _foundry_bin + os.pathsep + os.environ.get('PATH', '')


# ============================================================
# V3 Quote Math
# ============================================================

Q96 = 1 << 96


def quote_v3(sqrt_price_x96, liquidity, amount_in, decimals_in, decimals_out, zero_for_one):
    """
    Compute approximate V3 swap output using pure integer arithmetic.

    Returns (amount_out_raw, price_impact_bps)
    """
    sqrt_p = sqrt_price_x96

    if liquidity == 0:
        return 0, 10000
    if amount_in == 0:
        return 0, 0

    if zero_for_one:
        numerator = amount_in * liquidity * sqrt_p * sqrt_p
        denominator = Q96 * (liquidity * Q96 + amount_in * sqrt_p)
        if denominator == 0:
            return 0, 10000
        amount_out = numerator // denominator

        if amount_in > 0 and sqrt_p > 0:
            exec_bps = amount_out * Q96 * Q96 * 10000 // (amount_in * sqrt_p * sqrt_p)
            impact_bps = 10000 - exec_bps
        else:
            impact_bps = 10000
    else:
        numerator = amount_in * liquidity * Q96 * Q96
        denominator = sqrt_p * (liquidity * sqrt_p + amount_in * Q96)
        if denominator == 0:
            return 0, 10000
        amount_out = numerator // denominator

        if amount_in > 0 and sqrt_p > 0:
            exec_bps = amount_out * sqrt_p * sqrt_p * 10000 // (amount_in * Q96 * Q96)
            impact_bps = 10000 - exec_bps
        else:
            impact_bps = 10000

    if impact_bps < 0:
        impact_bps = 0
    if impact_bps > 10000:
        impact_bps = 10000

    return max(amount_out, 0), impact_bps


# ============================================================
# ABI Encoding
# ============================================================

def encode_uint256(val):
    return val.to_bytes(32, 'big').hex()


def encode_address(addr):
    addr = addr.lower()
    if addr.startswith('0x'):
        addr = addr[2:]
    return addr.zfill(64)


def encode_uint256_array(values):
    parts = [encode_uint256(len(values))]
    for v in values:
        parts.append(encode_uint256(v))
    return ''.join(parts)


def encode_address_array(addrs):
    parts = [encode_uint256(len(addrs))]
    for a in addrs:
        parts.append(encode_address(a))
    return ''.join(parts)


def encode_bytes(data_hex):
    if data_hex.startswith('0x'):
        data_hex = data_hex[2:]
    if len(data_hex) % 2 != 0:
        data_hex = '0' + data_hex
    byte_len = len(data_hex) // 2
    padded_len = ((byte_len + 31) // 32) * 32
    return encode_uint256(byte_len) + data_hex.ljust(padded_len * 2, '0')


def encode_bytes_array(items):
    n = len(items)
    head_parts = [encode_uint256(n)]
    data_start = 32 + n * 32
    data_parts = []
    current_offset = data_start
    for item in items:
        head_parts.append(encode_uint256(current_offset))
        item_encoded = encode_bytes(item)
        data_parts.append(item_encoded)
        current_offset += len(item_encoded) // 2
    return ''.join(head_parts) + ''.join(data_parts)


def encode_mix_swap_calldata(
    from_token, to_token, amount, min_return, expected,
    adapter, pool, router, fee, direction, deadline,
    wrapped_native=None
):
    """
    Encode mixSwap(...) with correct V3 extraData format.

    wrapped_native: address of wrapped native token (WPROS/WPHRS).
                    Used in extraData to resolve NATIVE → wrapped.
    """
    method_id = 'ff84aafa'

    # Resolve NATIVE → wrapped_native for extraData pool pair info
    if wrapped_native:
        pool_from = wrapped_native if from_token.lower() == NATIVE.lower() else from_token
        pool_to = wrapped_native if to_token.lower() == NATIVE.lower() else to_token
    else:
        pool_from = from_token
        pool_to = to_token

    # Fixed offsets (all sections have known sizes):
    # Head: 12 words = 384 = 0x180
    # mixAdapters: 2 words = 64
    # assetIds: 2 words = 64
    # pathIds: 3 words = 96
    # extraData: 9 words = 288
    # userData: 3 words = 96

    head = ''
    head += encode_address(from_token)        # [0]
    head += encode_address(to_token)          # [1]
    head += encode_uint256(amount)            # [2] fromTokenAmount
    head += encode_uint256(expected)          # [3] expReturnAmount
    head += encode_uint256(min_return)        # [4] minReturnAmount
    head += encode_uint256(0x180)             # [5] mixAdapters offset
    head += encode_uint256(0x1c0)             # [6] assetIds offset
    head += encode_uint256(0x200)             # [7] pathIds offset
    head += encode_uint256(direction)         # [8]
    head += encode_uint256(0x260)             # [9] extraData offset
    head += encode_uint256(0x380)             # [10] userData offset
    head += encode_uint256(deadline)          # [11]

    tail = ''
    # mixAdapters[]
    tail += encode_address_array([adapter])
    # assetIds[]
    tail += encode_address_array([pool])
    # pathIds[]
    tail += encode_address_array([adapter, router])

    # extraData[] — V3 pool pair info (fromToken, toToken, fee)
    tail += encode_uint256(1)                 # count
    tail += encode_uint256(0x20)              # offset to first element
    tail += encode_uint256(0xc0)              # length of bytes (192 = 6 words)
    tail += encode_uint256(0)                 # struct padding
    tail += encode_uint256(0x40)              # offset to tokenA
    tail += encode_uint256(0x60)              # offset to tokenB
    tail += encode_address(pool_from)         # tokenA (WPROS if NATIVE)
    tail += encode_address(pool_to)           # tokenB (WPROS if NATIVE)
    tail += encode_uint256(fee)               # fee tier

    # userData
    tail += encode_uint256(0x40)              # length (64 bytes)
    tail += encode_uint256(0)
    tail += encode_uint256(0)

    return '0x' + method_id + head + tail


# ============================================================
# Network Config & Token Registry
# ============================================================

NATIVE = '0x' + 'e' * 40  # 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee — standard DODO native token address

NETWORKS = {
    'mainnet': {
        'rpc': 'https://rpc.pharos.xyz',
        'explorer': 'https://pharosscan.xyz',
        'native_symbol': 'PROS',
        'tokens': {
            'PROS':  {'address': NATIVE, 'decimals': 18, 'wrapped': 'WPROS'},
            'WPROS': {'address': '0x52c48d4213107b20bc583832b0d951fb9ca8f0b0', 'decimals': 18},
            'USDC':  {'address': '0xc879c018db60520f4355c26ed1a6d572cdac1815', 'decimals': 6},
            'WETH':  {'address': '0x1f4b7011ee3d53969bb67f59428a9ec0477856e9', 'decimals': 18},
            'LINK':  {'address': '0x51e2a24742db77604b881d6781ee16b5b8fcbe29', 'decimals': 18},
        },
        'contracts': {
            'factory': '0x2c90ccb0b989afa2433f499698451a25744a552b',
            'router': '0xa5ca5fbe34e444f366b373170541ec6902b0f75c',
            'approve_proxy': '0x2afc65f51b8afd1db9618643f89f0b135eaaeeaa',
            'inner_proxy': '0xbf105f4ffbd3825f5433d074008b9a76237d849c',
            'v3_adapter': '0x4fd44181839d24e7c8f4d1b9288379109ec25fae',
        },
        'pools': [
            {
                'pair': ('WPROS', 'USDC'),
                'address': '0x912c9aDe24D44d8922f0866D8Dcb079f1363f647',
                'fee': 100,
                'token0': '0x52C48d4213107b20bC583832b0d951FB9CA8F0B0',
                'token1': '0xC879C018dB60520F4355C26eD1a6D572cdAC1815',
            },
            {
                'pair': ('WPROS', 'USDC'),
                'address': '0x4146D192Da6428c9e1C243D2A953c625B5765623',
                'fee': 3000,
                'token0': '0x52C48d4213107b20bC583832b0d951FB9CA8F0B0',
                'token1': '0xC879C018dB60520F4355C26eD1a6D572cdAC1815',
            },
        ],
    },
    'testnet': {
        'rpc': 'https://rpc.testnet.pharos.xyz',
        'explorer': 'https://testnet.pharosscan.xyz',
        'native_symbol': 'PHRS',
        'tokens': {
            'PHRS':  {'address': NATIVE, 'decimals': 18, 'wrapped': 'WPHRS'},
            'WPHRS': {'address': '0x838800b758277cc111b2d48ab01e5e164f8e9471', 'decimals': 18},
            'USDC':  {'address': '0xcfc8330f4bcab529c625d12781b1c19466a9fc8b', 'decimals': 6},
            'USDT':  {'address': '0xe7e84b8b4f39c507499c40b4ac199b050e2882d5', 'decimals': 6},
            'WETH':  {'address': '0x7d211f77525ea39a0592794f793cc1036eeaccd5', 'decimals': 18},
            'WBTC':  {'address': '0x0c64f03eea5c30946d5c55b4b532d08ad74638a4', 'decimals': 8},
        },
        'contracts': {
            'factory': '0x2c90ccb0b989afa2433f499698451a25744a552b',
            'router': '0xa5ca5fbe34e444f366b373170541ec6902b0f75c',
            'approve_proxy': '0x2afc65f51b8afd1db9618643f89f0b135eaaeeaa',
            'v3_adapter': '0x4fd44181839d24e7c8f4d1b9288379109ec25fae',
        },
        'pools': [],
    },
}


# ============================================================
# Cast Helpers
# ============================================================

def _cast(args, timeout=120):
    """Run cast command and return stdout."""
    result = subprocess.run(
        ['cast'] + args,
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def _first(output):
    """Parse first value from cast output."""
    return output.strip().split()[0] if output.strip() else ''


def _call(rpc, contract, sig, *args):
    """cast call contract.sig(args)"""
    return _cast(
        ['call', contract, sig] + [str(a) for a in args] + ['--rpc-url', rpc]
    )


def _send(rpc, private_key, to, sig=None, *args, value=None):
    """cast send transaction."""
    cmd = ['send', to]
    if sig:
        cmd.append(sig)
        cmd.extend([str(a) for a in args])
    cmd.extend(['--rpc-url', rpc, '--private-key', private_key, '--legacy'])
    if value:
        cmd.extend(['--value', str(value)])
    return _cast(cmd, timeout=300)


def _get_wallet(private_key):
    """Derive wallet address from private key."""
    return _cast(['wallet', 'address', '--private-key', private_key])


def _get_native_balance(rpc, address):
    """Get native token balance in wei."""
    return _cast(['balance', address, '--rpc-url', rpc])


def _parse_tx_hash(output):
    """Extract transactionHash from cast send output."""
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('transactionHash'):
            return line.split()[-1]
    return ''


# ============================================================
# Token / Pool Resolution
# ============================================================

def _resolve_token(net, symbol):
    """Resolve token symbol to (symbol, info)."""
    sym = symbol.upper()
    # Direct match
    if sym in net['tokens']:
        return sym, net['tokens'][sym]
    # Alias: native symbol -> native entry
    if sym == net['native_symbol']:
        for k, v in net['tokens'].items():
            if v.get('address') == NATIVE:
                return k, v
    return None, None


def _find_pool(net, from_sym, to_sym):
    """Find pool from hardcoded registry."""
    def _wrapped(sym):
        info = net['tokens'].get(sym)
        return info.get('wrapped', sym) if info else sym

    f, t = _wrapped(from_sym), _wrapped(to_sym)
    for pool in net['pools']:
        pair = pool['pair']
        if (f, t) == pair or (t, f) == pair:
            return pool
    return None


def _discover_pool(rpc, net, from_sym, to_sym):
    """Fallback: discover pool via Factory getPool."""
    from_info = net['tokens'].get(from_sym)
    to_info = net['tokens'].get(to_sym)
    if not from_info or not to_info:
        return None

    def _addr(info):
        if info.get('wrapped'):
            return net['tokens'][info['wrapped']]['address']
        return info['address']

    factory = net['contracts']['factory']
    best = None
    best_liq = 0

    for fee in [100, 500, 3000, 10000]:
        try:
            pool_addr = _first(_call(rpc, factory,
                'getPool(address,address,uint24)(address)',
                _addr(from_info), _addr(to_info), fee))
            if not pool_addr or pool_addr == '0x' + '0' * 40:
                continue
            liq = int(_first(_call(rpc, pool_addr, 'liquidity()(uint128)')))
            if liq > best_liq:
                t0 = _first(_call(rpc, pool_addr, 'token0()(address)'))
                t1 = _first(_call(rpc, pool_addr, 'token1()(address)'))
                best = {'address': pool_addr, 'fee': fee, 'token0': t0, 'token1': t1}
                best_liq = liq
        except Exception:
            continue
    return best


# ============================================================
# Swap Command
# ============================================================

def cmd_swap(args):
    net = NETWORKS[args.network]
    rpc = args.rpc or net['rpc']
    private_key = os.environ.get('PRIVATE_KEY', '')
    if not private_key:
        _fail('PRIVATE_KEY not set. Source .env file or set PRIVATE_KEY env var.')

    # Resolve tokens
    from_sym, from_info = _resolve_token(net, args.from_token)
    to_sym, to_info = _resolve_token(net, args.to_token)
    if not from_info or not to_info:
        _fail(f'Unknown token. Available: {", ".join(sorted(net["tokens"].keys()))}')

    # Parse amount
    is_native = from_info.get('address') == NATIVE
    if str(args.amount).lower() in ('all', 'max'):
        wallet = _get_wallet(private_key)
        if is_native:
            bal = int(_first(_get_native_balance(rpc, wallet)))
        else:
            bal = int(_first(_call(rpc, from_info['address'], 'balanceOf(address)(uint256)', wallet)))
        amount_raw = bal
        amount_float = bal / (10 ** from_info['decimals'])
    else:
        try:
            amount_float = float(args.amount)
        except ValueError:
            _fail(f'Invalid amount: {args.amount}')
        amount_raw = int(amount_float * (10 ** from_info['decimals']))

    from_decimals = from_info['decimals']
    to_decimals = to_info['decimals']

    if amount_raw <= 0:
        _fail('Amount must be greater than 0.')

    # Find pool (registry first, factory fallback)
    pool = _find_pool(net, from_sym, to_sym)
    if not pool:
        _log(f'Pool not in registry, discovering via Factory...')
        pool = _discover_pool(rpc, net, from_sym, to_sym)
    if not pool:
        _fail(f'No V3 pool found for {from_sym}/{to_sym}.')

    pool_addr = pool['address']

    # Read pool state
    _log(f'Reading pool {pool_addr[:10]}...')
    try:
        slot0_out = _call(rpc, pool_addr, 'slot0()(uint160,int24,uint16,uint16,uint16,uint8,bool)')
        sqrt_price = int(_first(slot0_out))
    except Exception as e:
        _fail(f'Failed to read pool state: {e}')

    try:
        liquidity = int(_first(_call(rpc, pool_addr, 'liquidity()(uint128)')))
    except Exception:
        liquidity = 0

    if liquidity == 0:
        _fail('Pool has zero liquidity.')

    # Determine swap direction
    token0 = pool['token0'].lower()
    from_compare = from_info['address'].lower()
    if is_native and from_info.get('wrapped'):
        from_compare = net['tokens'][from_info['wrapped']]['address'].lower()
    zero_for_one = (from_compare == token0)

    # Quote
    amount_out_raw, impact_bps = quote_v3(
        sqrt_price, liquidity, amount_raw, from_decimals, to_decimals, zero_for_one
    )

    # Safety: price impact
    if impact_bps > 300:
        _fail(f'Price impact too high: {impact_bps / 100:.2f}% > 3%. Try a smaller amount.')

    if amount_out_raw <= 0:
        _fail('Quote returned 0. Pool may lack liquidity for this amount.')

    # Safety: balance check
    wallet = _get_wallet(private_key)
    if is_native:
        bal = int(_first(_get_native_balance(rpc, wallet)))
        # Leave 0.1 native for gas (BlockWaver standard)
        gas_reserve = int(0.1 * (10 ** from_decimals))
        if bal - gas_reserve < amount_raw:
            _fail(f'Insufficient {from_sym}. Have: {bal / (10**from_decimals):.6f}, need: {amount_float} + gas reserve.')
    else:
        bal = int(_first(_call(rpc, from_info['address'], 'balanceOf(address)(uint256)', wallet)))
        if bal < amount_raw:
            _fail(f'Insufficient {from_sym}. Have: {bal / (10**from_decimals):.6f}, need: {amount_float}.')

    # Calculate min return (0.5% slippage)
    min_return = amount_out_raw * 995 // 1000
    deadline = int(time.time()) + 600

    amount_out_human = amount_out_raw / (10 ** to_decimals)

    # Native token: send PROS as value (no wrap needed)
    # ERC20: approve exact amount via DODO Approve Proxy
    actual_from = from_info['address']
    send_value = None
    if is_native:
        send_value = str(amount_raw)
        # fromToken stays as NATIVE (0xEeeee...), router handles wrapping
    else:
        _log(f'Approving {from_sym}...')
        # Approve inner_proxy — it's the one that does transferFrom
        _send(rpc, private_key, actual_from, 'approve(address,uint256)',
              net['contracts']['inner_proxy'], str(amount_raw))

    # Encode mixSwap calldata with pool pair info in extraData
    direction = 0 if zero_for_one else 1
    wrapped_native = net['tokens'].get('WPROS', net['tokens'].get('WPHRS', {})).get('address')
    calldata = encode_mix_swap_calldata(
        actual_from, to_info['address'], amount_raw, min_return, amount_out_raw,
        net['contracts']['v3_adapter'], pool_addr, net['contracts']['router'],
        pool['fee'], direction, deadline,
        wrapped_native=wrapped_native
    )

    _log(f'Swapping {amount_float} {from_sym} -> ~{amount_out_human:.6f} {to_sym}...')
    result = _send(rpc, private_key, net['contracts']['router'], calldata, value=send_value)
    tx_hash = _parse_tx_hash(result)

    output = {
        'success': True,
        'action': 'swap',
        'from': from_sym,
        'to': to_sym,
        'amountIn': amount_float,
        'amountOut': round(amount_out_human, 6),
        'rate': round(amount_out_human / amount_float, 6) if amount_float > 0 else 0,
        'priceImpactBps': impact_bps,
        'pool': pool_addr,
        'fee': pool['fee'],
        'txHash': tx_hash,
        'explorer': f"{net['explorer']}/tx/{tx_hash}" if tx_hash else '',
    }
    print(json.dumps(output, indent=2))


# ============================================================
# Balance Command
# ============================================================

def cmd_balance(args):
    net = NETWORKS[args.network]
    rpc = args.rpc or net['rpc']
    private_key = os.environ.get('PRIVATE_KEY', '')
    if not private_key:
        _fail('PRIVATE_KEY not set.')

    wallet = _get_wallet(private_key)
    balances = {}

    # Native balance
    try:
        bal_wei = int(_first(_get_native_balance(rpc, wallet)))
        native_sym = net['native_symbol']
        if bal_wei > 0:
            balances[native_sym] = bal_wei / (10 ** 18)
    except Exception:
        pass

    # ERC20 balances
    for sym, info in net['tokens'].items():
        if info.get('address') == NATIVE:
            continue
        try:
            bal = int(_first(_call(rpc, info['address'], 'balanceOf(address)(uint256)', wallet)))
            if bal > 0:
                balances[sym] = bal / (10 ** info['decimals'])
        except Exception:
            pass

    output = {
        'success': True,
        'action': 'balance',
        'wallet': wallet,
        'balances': {k: round(v, 6) for k, v in sorted(balances.items())},
        'network': args.network,
    }
    print(json.dumps(output, indent=2))


# ============================================================
# Send Command
# ============================================================

def cmd_send(args):
    net = NETWORKS[args.network]
    rpc = args.rpc or net['rpc']
    private_key = os.environ.get('PRIVATE_KEY', '')
    if not private_key:
        _fail('PRIVATE_KEY not set.')

    token_sym, token_info = _resolve_token(net, args.token)
    if not token_info:
        _fail(f'Unknown token. Available: {", ".join(sorted(net["tokens"].keys()))}')

    try:
        amount_float = float(args.amount)
    except ValueError:
        _fail(f'Invalid amount: {args.amount}')
    amount_raw = int(amount_float * (10 ** token_info['decimals']))
    to_addr = args.to

    # Balance check
    wallet = _get_wallet(private_key)
    is_native = token_info.get('address') == NATIVE
    if is_native:
        bal = int(_first(_get_native_balance(rpc, wallet)))
        if bal < amount_raw:
            _fail(f'Insufficient {token_sym}. Have: {bal/(10**token_info["decimals"]):.6f}, need: {amount_float}.')
        _log(f'Sending {amount_float} {token_sym} to {to_addr}...')
        result = _send(rpc, private_key, to_addr, value=str(amount_raw))
    else:
        bal = int(_first(_call(rpc, token_info['address'], 'balanceOf(address)(uint256)', wallet)))
        if bal < amount_raw:
            _fail(f'Insufficient {token_sym}. Have: {bal/(10**token_info["decimals"]):.6f}, need: {amount_float}.')
        _log(f'Sending {amount_float} {token_sym} to {to_addr}...')
        result = _send(rpc, private_key, token_info['address'],
                       'transfer(address,uint256)', to_addr, str(amount_raw))

    tx_hash = _parse_tx_hash(result)
    output = {
        'success': True,
        'action': 'send',
        'token': token_sym,
        'amount': amount_float,
        'to': to_addr,
        'txHash': tx_hash,
        'explorer': f"{net['explorer']}/tx/{tx_hash}" if tx_hash else '',
    }
    print(json.dumps(output, indent=2))


# ============================================================
# Helpers
# ============================================================

def _fail(msg):
    print(json.dumps({'error': msg}), file=sys.stdout)
    sys.exit(1)


def _log(msg):
    print(msg, file=sys.stderr)


# ============================================================
# CLI
# ============================================================

def cmd_quote(args):
    out, impact = quote_v3(
        args.sqrt_price, args.liquidity, args.amount,
        args.decimals_in, args.decimals_out,
        args.zero_for_one
    )
    print(json.dumps({"amountOut": out, "priceImpactBps": impact}))


def cmd_encode(args):
    calldata = encode_mix_swap_calldata(
        args.from_token, args.to_token, args.amount,
        args.min_return, args.expected,
        args.adapter, args.pool, args.router,
        args.fee, args.direction, args.deadline,
        wrapped_native=getattr(args, 'wrapped_native', None)
    )
    print(calldata)


def main():
    parser = argparse.ArgumentParser(description='FaroSwap V3 helpers')
    sub = parser.add_subparsers(dest='command')

    # quote subcommand
    p_quote = sub.add_parser('quote')
    p_quote.add_argument('--sqrt-price', type=int, required=True)
    p_quote.add_argument('--liquidity', type=int, required=True)
    p_quote.add_argument('--amount', type=int, required=True)
    p_quote.add_argument('--decimals-in', type=int, default=18)
    p_quote.add_argument('--decimals-out', type=int, default=18)
    p_quote.add_argument('--zero-for-one', type=lambda x: x.lower() == 'true', required=True)

    # encode subcommand
    p_enc = sub.add_parser('encode')
    p_enc.add_argument('--from-token', required=True)
    p_enc.add_argument('--to-token', required=True)
    p_enc.add_argument('--amount', type=int, required=True)
    p_enc.add_argument('--min-return', type=int, required=True)
    p_enc.add_argument('--expected', type=int, required=True)
    p_enc.add_argument('--pool', required=True)
    p_enc.add_argument('--fee', type=int, required=True)
    p_enc.add_argument('--adapter', required=True)
    p_enc.add_argument('--router', required=True)
    p_enc.add_argument('--direction', type=int, required=True)
    p_enc.add_argument('--deadline', type=int, required=True)
    p_enc.add_argument('--wrapped-native', default=None)

    # swap subcommand
    p_swap = sub.add_parser('swap')
    p_swap.add_argument('--from', dest='from_token', required=True)
    p_swap.add_argument('--to', dest='to_token', required=True)
    p_swap.add_argument('--amount', required=True)
    p_swap.add_argument('--network', default='mainnet', choices=['mainnet', 'testnet'])
    p_swap.add_argument('--rpc', default=None)

    # balance subcommand
    p_bal = sub.add_parser('balance')
    p_bal.add_argument('--network', default='mainnet', choices=['mainnet', 'testnet'])
    p_bal.add_argument('--rpc', default=None)

    # send subcommand
    p_send = sub.add_parser('send')
    p_send.add_argument('--token', required=True)
    p_send.add_argument('--amount', required=True)
    p_send.add_argument('--to', required=True)
    p_send.add_argument('--network', default='mainnet', choices=['mainnet', 'testnet'])
    p_send.add_argument('--rpc', default=None)

    args = parser.parse_args()

    if args.command == 'quote':
        cmd_quote(args)
    elif args.command == 'encode':
        cmd_encode(args)
    elif args.command == 'swap':
        cmd_swap(args)
    elif args.command == 'balance':
        cmd_balance(args)
    elif args.command == 'send':
        cmd_send(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
