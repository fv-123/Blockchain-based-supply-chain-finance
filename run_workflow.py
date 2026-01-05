#!/usr/bin/env python3
import json, time, sys
from web3 import Web3
from pathlib import Path
from config.config_template import RPC, CHAIN_ID, CONTRACT_ADDRESS


# load local secrets
try:
   from config.config_local import ADMIN_PRIVATE_KEY, SUPPLIER_PRIVATE_KEY, FINANCIER_PRIVATE_KEY, ADMIN_ADDRESS, SUPPLIER_ADDRESS, FINANCIER_ADDRESS, DEBTOR_ADDRESS
except Exception as e:
   print("ERROR: missing config_local.py with private keys and addresses")
   sys.exit(1)


w3 = Web3(Web3.HTTPProvider(RPC))
if not w3.isConnected():
   print("ERROR: cannot connect to RPC:", RPC)
   sys.exit(1)


abi_path = Path(__file__).resolve().parents[1] / "abi" / "InvoiceToken.json"
with open(abi_path) as f:
   abi = json.load(f)


contract = w3.eth.contract(address=Web3.toChecksumAddress(CONTRACT_ADDRESS), abi=abi)


def addr_from_pk(pk):
   return w3.eth.account.from_key(pk).address


admin = addr_from_pk(ADMIN_PRIVATE_KEY)
supplier = addr_from_pk(SUPPLIER_PRIVATE_KEY)
financier = addr_from_pk(FINANCIER_PRIVATE_KEY)


def send_and_wait(tx, pk):
   tx['nonce'] = w3.eth.get_transaction_count(w3.eth.account.from_key(pk).address)
   signed = w3.eth.account.sign_transaction(tx, pk)
   txh = w3.eth.send_raw_transaction(signed.rawTransaction)
   print("Sent tx:", txh.hex())
   r = w3.eth.wait_for_transaction_receipt(txh)
   print("Mined:", r.transactionHash.hex(), "gasUsed:", r.gasUsed)
   return r


def main():
   print("Admin:", admin)
   print("Supplier:", supplier)
   print("Financier:", financier)
   print("Contract:", CONTRACT_ADDRESS)


   # authorize supplier
   tx = contract.functions.authorizeSupplier(Web3.toChecksumAddress(supplier), True).buildTransaction({
       "from": admin, "gas": 200000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID
   })
   r1 = send_and_wait(tx, ADMIN_PRIVATE_KEY)
   time.sleep(0.3)


   # authorize financier
   tx = contract.functions.authorizeFinancier(Web3.toChecksumAddress(financier), True).buildTransaction({
       "from": admin, "gas": 200000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID
   })
   r2 = send_and_wait(tx, ADMIN_PRIVATE_KEY)
   time.sleep(0.3)


   # mint invoice
   dueDate = 1735689600
   tx = contract.functions.mintInvoice(Web3.toChecksumAddress(DEBTOR_ADDRESS), 100000, dueDate, "ipfs://example").buildTransaction({
       "from": supplier, "gas": 500000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID
   })
   r3 = send_and_wait(tx, SUPPLIER_PRIVATE_KEY)
   time.sleep(0.3)


   invoiceId = 1


   # transfer to financier
   tx = contract.functions.transferToFinancier(invoiceId, Web3.toChecksumAddress(financier)).buildTransaction({
       "from": supplier, "gas": 300000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID
   })
   r4 = send_and_wait(tx, SUPPLIER_PRIVATE_KEY)
   time.sleep(0.3)


   # mark settled
   tx = contract.functions.markSettled(invoiceId).buildTransaction({
       "from": admin, "gas": 200000, "gasPrice": w3.toWei("20","gwei"), "chainId": CHAIN_ID
   })
   r5 = send_and_wait(tx, ADMIN_PRIVATE_KEY)


   inv = contract.functions.getInvoice(invoiceId).call()
   owner = contract.functions.ownerOf(invoiceId).call()
   print("Final invoice:", inv)
   print("Owner:", owner)


   # save summary
   out = Path(__file__).resolve().parents[1] / "deployment" / "run_output.txt"
   with open(out, "w") as fh:
       fh.write(f"txs: {r1.transactionHash.hex()}, {r2.transactionHash.hex()}, {r3.transactionHash.hex()}, {r4.transactionHash.hex()}, {r5.transactionHash.hex()}\n")
       fh.write(f"gasUsed: {r1.gasUsed},{r2.gasUsed},{r3.gasUsed},{r4.gasUsed},{r5.gasUsed}\n")
       fh.write(f"final_invoice: {inv}\nowner: {owner}\n")
   print("Run output saved to", out)


if __name__ == "__main__":
   main()
