"""
FaroSwap V3 helpers for Pharos DEX Swap Skill.

Two commands:
  python3 helpers.py quote --sqrt-price X --liquidity Y --amount Z --decimals-in D --decimals-out D --zero-for-one [true|false]
  python3 helpers.py encode --from-token A --to-token A --amount N --min-return N --expected N --pool A --fee N --adapter A --router A --direction N --deadline N
"""
import sys
import argparse
import json
import struct


# ============================================================
# V3 Quote Math
# ============================================================

Q96 = 1 << 96


def quote_v3(sqrt_price_x96, liquidity, amount_in, decimals_in, decimals_out, zero_for_one):
    """
    Compute approximate V3 swap output using pure integer arithmetic.

    Returns (amount_out_raw, price_impact_bps)
      amount_out_raw: output amount in smallest token units
      price_impact_bps: price impact in basis points (0-10000)
    """
    sqrt_p = sqrt_price_x96

    if liquidity == 0:
        return 0, 10000
    if amount_in == 0:
        return 0, 0

    if zero_for_one:
        # Selling token0, receiving token1
        # amountOut = (amountIn * L * sqrtP^2) / (Q96 * (L * Q96 + amountIn * sqrtP))
        numerator = amount_in * liquidity * sqrt_p * sqrt_p
        denominator = Q96 * (liquidity * Q96 + amount_in * sqrt_p)
        if denominator == 0:
            return 0, 10000
        amount_out = numerator // denominator

        # Price impact: spot = sqrtP^2/Q96^2 (token1 per token0 raw)
        # impact = 1 - (amountOut/amountIn) / spot
        if amount_in > 0 and sqrt_p > 0:
            exec_bps = amount_out * Q96 * Q96 * 10000 // (amount_in * sqrt_p * sqrt_p)
            impact_bps = 10000 - exec_bps
        else:
            impact_bps = 10000
    else:
        # Selling token1, receiving token0
        # amountOut = (amountIn * L * Q96^2) / (sqrtP * (L * sqrtP + amountIn * Q96))
        numerator = amount_in * liquidity * Q96 * Q96
        denominator = sqrt_p * (liquidity * sqrt_p + amount_in * Q96)
        if denominator == 0:
            return 0, 10000
        amount_out = numerator // denominator

        # Price impact: spot = Q96^2/sqrtP^2 (token0 per token1 raw)
        # impact = 1 - (amountOut/amountIn) / spot
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
    """Encode uint256[] as hex string (without 0x prefix)."""
    parts = [encode_uint256(len(values))]
    for v in values:
        parts.append(encode_uint256(v))
    return ''.join(parts)


def encode_address_array(addrs):
    """Encode address[] as hex string (without 0x prefix)."""
    parts = [encode_uint256(len(addrs))]
    for a in addrs:
        parts.append(encode_address(a))
    return ''.join(parts)


def encode_bytes(data_hex):
    """Encode bytes: uint256 length + data padded to 32 bytes."""
    if data_hex.startswith('0x'):
        data_hex = data_hex[2:]
    if len(data_hex) % 2 != 0:
        data_hex = '0' + data_hex
    byte_len = len(data_hex) // 2
    padded_len = ((byte_len + 31) // 32) * 32
    return encode_uint256(byte_len) + data_hex.ljust(padded_len * 2, '0')


def encode_bytes_array(items):
    """Encode bytes[] as hex string."""
    n = len(items)
    # Head: count + n offsets
    head_parts = [encode_uint256(n)]

    # Calculate offsets
    # After count (32 bytes), there are n offset values (each 32 bytes)
    # Then the actual bytes data starts
    data_start = 32 + n * 32  # byte offset where first bytes element data starts

    data_parts = []
    current_offset = data_start

    for item in items:
        head_parts.append(encode_uint256(current_offset))
        item_encoded = encode_bytes(item)
        data_parts.append(item_encoded)
        current_offset += len(item_encoded) // 2  # each hex char pair = 1 byte

    return ''.join(head_parts) + ''.join(data_parts)


def encode_mix_swap_calldata(
    from_token, to_token, amount, min_return, expected,
    adapter, pool, router, fee, direction, deadline
):
    """
    Encode mixSwap(address,address,uint256,uint256,uint256,address[],address[],address[],uint256,bytes[],bytes,uint256)

    Returns the full calldata hex string WITH 0x prefix and method ID.
    """
    method_id = 'ff84aafa'

    # Encode extraData: single bytes element containing abi.encode(uint256(0xc0))
    extra_data = encode_bytes_array(['0' * 63 + 'c0'])  # 0x00...c0 = uint256(192)

    # Encode userData: abi.encode(uint256(0), uint256(0)) = 64 bytes of zeros
    user_data = '0' * 128  # 64 bytes = 128 hex chars

    # Build the full ABI-encoded data
    # Head: 12 params * 32 bytes = 384 bytes
    # Param layout:
    # 0: address fromToken
    # 1: address toToken
    # 2: uint256 fromTokenAmount
    # 3: uint256 minReturnAmount
    # 4: uint256 expectedAmount
    # 5: uint256 offset to mixAdapters[]
    # 6: uint256 offset to assetIds[]
    # 7: uint256 offset to pathIds[]
    # 8: uint256 directions
    # 9: uint256 offset to extraData[]
    # 10: uint256 offset to userData
    # 11: uint256 deadline

    # Calculate offsets
    head_size = 12 * 32  # 384 bytes

    # mixAdapters[] data: count(32) + 1 address(32) = 64 bytes
    mix_adapters_size = 32 + 32
    off_mix_adapters = head_size

    # assetIds[] data: count(32) + 1 address(32) = 64 bytes
    off_asset_ids = off_mix_adapters + mix_adapters_size

    # pathIds[] data: count(32) + 2 addresses(64) = 96 bytes
    path_ids_size = 32 + 2 * 32
    off_path_ids = off_asset_ids + 32 + 32

    # directions: inline (no offset needed) — it's a uint256

    # extraData[] data: variable
    off_extra_data = off_path_ids + path_ids_size

    # userData data: variable
    off_user_data = off_extra_data + len(extra_data) // 2

    # Build head
    head = ''
    head += encode_address(from_token)        # [0]
    head += encode_address(to_token)          # [1]
    head += encode_uint256(amount)            # [2]
    head += encode_uint256(min_return)        # [3]
    head += encode_uint256(expected)          # [4]
    head += encode_uint256(off_mix_adapters)  # [5]
    head += encode_uint256(off_asset_ids)     # [6]
    head += encode_uint256(off_path_ids)      # [7]
    head += encode_uint256(direction)         # [8]
    head += encode_uint256(off_extra_data)    # [9]
    head += encode_uint256(off_user_data)     # [10]
    head += encode_uint256(deadline)          # [11]

    # Build tail
    tail = ''
    # mixAdapters[]: count + [adapter]
    tail += encode_address_array([adapter])
    # assetIds[]: count + [pool]
    tail += encode_address_array([pool])
    # pathIds[]: count + [adapter, router]
    tail += encode_address_array([adapter, router])
    # extraData[]
    tail += extra_data
    # userData
    tail += encode_bytes(user_data)

    return '0x' + method_id + head + tail


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
        args.fee, args.direction, args.deadline
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

    args = parser.parse_args()

    if args.command == 'quote':
        cmd_quote(args)
    elif args.command == 'encode':
        cmd_encode(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
