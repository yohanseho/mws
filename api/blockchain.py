import asyncio
import logging
from typing import List, Dict, Any
from web3 import Web3
from web3.exceptions import TransactionNotFound
import aiohttp
import json

class BlockchainService:
    """Service for blockchain interactions using Web3.py"""
    
    def __init__(self):
        self.predefined_networks = {
            'ethereum': {
                'name': 'Ethereum Mainnet',
                'rpc_url': 'https://eth.llamarpc.com',
                'chain_id': 1,
                'symbol': 'ETH',
                'explorer': 'https://etherscan.io'
            },
            'sepolia': {
                'name': 'Sepolia Testnet',
                'rpc_url': 'https://ethereum-sepolia-rpc.publicnode.com',
                'chain_id': 11155111,
                'symbol': 'ETH',
                'explorer': 'https://sepolia.etherscan.io'
            },
            'holesky': {
                'name': 'Holesky Testnet',
                'rpc_url': 'https://ethereum-holesky.publicnode.com',
                'chain_id': 17000,
                'symbol': 'ETH',
                'explorer': 'https://holesky.etherscan.io'
            },
            'monad': {
                'name': 'Monad Testnet',
                'rpc_url': 'https://testnet-rpc.monad.xyz',
                'chain_id': 41454,
                'symbol': 'MON',
                'explorer': 'https://testnet-explorer.monad.xyz'
            }
        }
    
    def get_address_from_private_key(self, private_key: str) -> str:
        """Generate wallet address from private key"""
        try:
            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            return account.address
        except Exception as e:
            logging.error(f"Error generating address: {e}")
            raise
    
    def get_web3_instance(self, network_config: Dict[str, Any]) -> Web3:
        """Create Web3 instance for given network"""
        rpc_url = network_config.get('rpc_url')
        if not rpc_url:
            raise ValueError("RPC URL is required")
        
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Verify connection
        if not w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        return w3
    
    async def get_balance_async(self, address: str, network_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get balance for a single address asynchronously"""
        try:
            rpc_url = network_config.get('rpc_url')
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                
                async with session.post(str(rpc_url), json=payload) as response:
                    data = await response.json()
                    
                    if 'error' in data:
                        raise Exception(f"RPC Error: {data['error']}")
                    
                    balance_wei = int(data['result'], 16)
                    balance_eth = balance_wei / 10**18
                    
                    return {
                        'address': address,
                        'balance_wei': balance_wei,
                        'balance_eth': balance_eth,
                        'balance_formatted': f"{balance_eth:.6f}"
                    }
        except Exception as e:
            logging.error(f"Error getting balance for {address}: {e}")
            return {
                'address': address,
                'balance_wei': 0,
                'balance_eth': 0,
                'balance_formatted': "0.000000",
                'error': str(e)
            }
    
    async def get_balances_async(self, addresses: List[str], network_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get balances for multiple addresses concurrently"""
        tasks = [self.get_balance_async(addr, network_config) for addr in addresses]
        return await asyncio.gather(*tasks)
    
    async def estimate_gas_async(self, w3: Web3, transaction: Dict[str, Any]) -> int:
        """Estimate gas for transaction"""
        try:
            return w3.eth.estimate_gas(transaction)  # type: ignore
        except Exception as e:
            logging.warning(f"Gas estimation failed: {e}, using default")
            return 21000  # Standard ETH transfer gas limit
    
    async def send_transaction_async(self, wallet: Dict[str, Any], network_config: Dict[str, Any], 
                                   percentage: int, recipient_address: str) -> Dict[str, Any]:
        """Send transaction from a single wallet"""
        try:
            w3 = self.get_web3_instance(network_config)
            private_key = wallet['private_key']
            from_address = wallet['address']
            
            # Get current balance
            balance_wei = w3.eth.get_balance(from_address)
            
            if balance_wei == 0:
                return {
                    'wallet': from_address,
                    'status': 'failed',
                    'error': 'Insufficient balance',
                    'amount': '0',
                    'tx_hash': None
                }
            
            # Get current nonce
            nonce = w3.eth.get_transaction_count(from_address)
            
            # Get gas price
            gas_price = w3.eth.gas_price
            
            # Estimate gas for the transaction
            estimated_gas = await self.estimate_gas_async(w3, {
                'from': from_address,
                'to': recipient_address,
                'value': 1  # Small value for estimation
            })
            
            # Calculate total gas cost
            gas_cost = estimated_gas * gas_price
            
            # Calculate amount to send based on percentage
            if percentage == 100:  # MAX
                amount_to_send = balance_wei - gas_cost
            else:
                amount_to_send = (balance_wei * percentage) // 100
            
            # Ensure we have enough for gas
            if amount_to_send <= 0 or (amount_to_send + gas_cost) > balance_wei:
                return {
                    'wallet': from_address,
                    'status': 'failed',
                    'error': 'Insufficient balance for transaction + gas',
                    'amount': '0',
                    'tx_hash': None
                }
            
            # Build transaction
            transaction = {
                'nonce': nonce,
                'to': recipient_address,
                'value': amount_to_send,
                'gas': estimated_gas,
                'gasPrice': gas_price,
                'chainId': network_config['chain_id']
            }
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            # Convert amount to ETH for display
            amount_eth = amount_to_send / 10**18
            
            return {
                'wallet': from_address,
                'status': 'success',
                'error': None,
                'amount': f"{amount_eth:.6f}",
                'tx_hash': tx_hash_hex,
                'explorer_url': f"{network_config.get('explorer', '')}/tx/{tx_hash_hex}"
            }
            
        except Exception as e:
            logging.error(f"Error sending transaction from {wallet['address']}: {e}")
            return {
                'wallet': wallet['address'],
                'status': 'failed',
                'error': str(e),
                'amount': '0',
                'tx_hash': None
            }
    
    async def send_transactions_async(self, wallets: List[Dict[str, Any]], network_config: Dict[str, Any],
                                    percentage: int, recipient_address: str) -> List[Dict[str, Any]]:
        """Send transactions from multiple wallets concurrently"""
        tasks = [
            self.send_transaction_async(wallet, network_config, percentage, recipient_address)
            for wallet in wallets
        ]
        return await asyncio.gather(*tasks)
    
    def get_predefined_networks(self) -> Dict[str, Dict[str, Any]]:
        """Get list of predefined networks"""
        return self.predefined_networks
