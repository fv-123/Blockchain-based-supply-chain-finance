#!/usr/bin/env python3
import json, sys
from web3 import Web3
from pathlib import Path
from config.config_template import RPC, CHAIN_ID, CONTRACT_ADDRESS
try:
   from config.config_local import ADMIN_PRIVATE_KEY, SUPPLIER_PRIVATE_KEY, FINANCIER_PRIVATE_KEY, ADMIN_ADDRESS, SUPPLIER_ADDRESS, FINANCIER_ADDRESS, DEBTOR_ADDRESS
except:
   print("Missing config_local")
   sys.exit(1)


w3 = Web3(Web3.HTTPProvider(RPC))
abi = json.load(open(Path(__file__).resolve().parents[1]/"abi"/"InvoiceToken.json"))
contract = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=abi)


def attempt_unauthorized_mint():
   # try minting with financier (not authorized supplier)
   pk = FINANCIER_PRIVATE_KEY
   acct = w3.eth.account.from_key(pk)
   try:
       tx = contract.functions.mintInvoice(Web3.toChecksumAddress(DEBTOR_ADDRESS), 1, 1735689600, "").buildTransaction({
           "from": acct.address, "gas": 400000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID, "nonce": w3.eth.get_transaction_count(acct.address)
       })
       signed = w3.eth.account.sign_transaction(tx, pk)
       h = w3.eth.send_raw_transaction(signed.rawTransaction)
       w3.eth.wait_for_transaction_receipt(h)
       print("ERROR: unauthorized mint unexpectedly succeeded")
   except Exception as e:
       print("Expected revert for unauthorized mint:", str(e))


def attempt_nonadmin_settle():
   pk = SUPPLIER_PRIVATE_KEY
   acct = w3.eth.account.from_key(pk)
   try:
       tx = contract.functions.markSettled(1).buildTransaction({
           "from": acct.address, "gas": 200000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID, "nonce": w3.eth.get_transaction_count(acct.address)
       })
       signed = w3.eth.account.sign_transaction(tx, pk)
       h = w3.eth.send_raw_transaction(signed.rawTransaction)
       w3.eth.wait_for_transaction_receipt(h)
       print("ERROR: non-admin settle unexpectedly succeeded")
   except Exception as e:
       print("Expected revert for non-admin settle:", str(e))


if __name__ == "__main__":
   attempt_unauthorized_mint()
   attempt_nonadmin_settle()
