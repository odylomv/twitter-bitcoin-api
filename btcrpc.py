from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

import secret as s

testnet_rpc = AuthServiceProxy(f"{s.RPC_PROTOCOL}://{s.RPC_USER}:{s.RPC_PASS}@{s.RPC_HOST}:{s.RPC_PORT}", timeout=120)


def send_raw_transaction(tx_hex: str) -> str:
    try:
        tx_id = testnet_rpc.sendrawtransaction(tx_hex)
        return tx_id
    except JSONRPCException as err:
        return err.message
