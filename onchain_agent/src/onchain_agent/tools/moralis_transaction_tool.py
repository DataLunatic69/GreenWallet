from typing import Type, Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import os
from datetime import datetime


class MoralisTransactionToolInput(BaseModel):
    """Input schema for Moralis Transaction Tool."""
    address: str = Field(..., description="Blockchain address to fetch transaction history for")
    chain: str = Field("eth", description="Blockchain to query (eth, polygon, bsc, arbitrum, optimism, base)")
    limit: int = Field(100, description="Maximum number of transactions to return (default: 100)")


class MoralisTransactionTool(BaseTool):
    """Tool to fetch transaction history using Moralis API."""
    name: str = "Moralis Transaction History Tool"
    description: str = (
        "Fetches comprehensive transaction history for a blockchain address using Moralis API. "
        "Returns transaction data including gas usage, timestamps, and transaction types. "
        "Essential for calculating carbon footprint based on actual on-chain activity."
    )
    args_schema: Type[BaseModel] = MoralisTransactionToolInput
    
    def __init__(self):
        """Initialize the MoralisTransactionTool with cache."""
        super().__init__()
        self._cache = {}
    
    def _cache_key(self, address: str, chain: str, limit: int) -> str:
        """Generate a cache key based on input parameters."""
        return f"{address.lower()}:{chain.lower()}:{limit}"
    
    def _get_api_key(self) -> str:
        """Get Moralis API key from environment."""
        api_key = os.getenv("MORALIS_API_KEY")
        if not api_key:
            raise ValueError("MORALIS_API_KEY environment variable not set")
        return api_key
    
    def _map_chain_name(self, chain: str) -> str:
        """Map common chain names to Moralis chain identifiers."""
        chain_map = {
            "ethereum": "eth",
            "eth": "eth",
            "polygon": "polygon",
            "matic": "polygon",
            "bsc": "bsc",
            "bnb": "bsc",
            "binance": "bsc",
            "arbitrum": "arbitrum",
            "optimism": "optimism",
            "base": "base",
            "avalanche": "avalanche",
            "avax": "avalanche"
        }
        return chain_map.get(chain.lower(), "eth")
    
    def _run(self, address: str, chain: str = "eth", limit: int = 100) -> str:
        """Fetch transaction history from Moralis API with caching."""
        # Check cache first
        cache_key = self._cache_key(address, chain, limit)
        if cache_key in self._cache:
            return f"[CACHED] {self._cache[cache_key]}"
        
        try:
            # Get API key
            api_key = self._get_api_key()
            
            # Map chain name
            chain_id = self._map_chain_name(chain)
            
            # Construct API URL
            url = f"https://deep-index.moralis.io/api/v2.2/{address}"
            
            # Set up headers and parameters
            headers = {
                "accept": "application/json",
                "X-API-Key": api_key
            }
            
            params = {
                "chain": chain_id,
                "limit": limit
            }
            
            # Make API request
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Format the response
            formatted_result = self._format_transaction_data(data, address, chain_id)
            
            # Cache the result
            self._cache[cache_key] = formatted_result
            
            return formatted_result
            
        except requests.exceptions.RequestException as e:
            return f"Error fetching transaction data from Moralis: {str(e)}"
        except Exception as e:
            return f"Error processing transaction data: {str(e)}"
    
    def _format_transaction_data(self, data: Dict[str, Any], address: str, chain: str) -> str:
        """Format transaction data into a readable string with gas usage details."""
        if not data or "result" not in data:
            return f"No transaction history found for {address} on {chain}."
        
        # Ensure all text is properly encoded
        def safe_str(value):
            """Convert value to string with proper encoding handling."""
            if value is None:
                return "Unknown"
            try:
                return str(value).encode('utf-8', errors='ignore').decode('utf-8')
            except:
                return "Unknown"
        
        transactions = data.get("result", [])
        
        if not transactions:
            return f"No transactions found for {address} on {chain}."
        
        # Calculate aggregate statistics
        total_transactions = len(transactions)
        total_gas_used = sum(int(tx.get("receipt_gas_used", 0)) for tx in transactions if tx.get("receipt_gas_used"))
        
        # Extract transaction types
        transaction_types = {}
        for tx in transactions:
            # Determine transaction type based on input data and value
            if tx.get("input") and tx.get("input") != "0x":
                tx_type = "contract_interaction"
            elif int(tx.get("value", "0")) > 0:
                tx_type = "simple_transfer"
            else:
                tx_type = "other"
            
            transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1
        
        # Format summary
        summary = [
            f"Transaction History for {address} on {chain.upper()}:",
            f"\nSummary Statistics:",
            f"  Total Transactions: {total_transactions:,}",
            f"  Total Gas Used: {total_gas_used:,}",
            f"  Average Gas per Transaction: {total_gas_used // total_transactions if total_transactions > 0 else 0:,}",
            f"\nTransaction Type Breakdown:"
        ]
        
        for tx_type, count in sorted(transaction_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
            summary.append(f"  {tx_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Add recent transactions sample
        summary.append(f"\nRecent Transactions (latest {min(5, total_transactions)}):")
        
        for idx, tx in enumerate(transactions[:5], 1):
            block_timestamp = tx.get("block_timestamp", "Unknown")
            if block_timestamp != "Unknown":
                try:
                    dt = datetime.fromisoformat(block_timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = block_timestamp
            else:
                time_str = "Unknown time"
            
            tx_hash = safe_str(tx.get("hash", "Unknown"))[:16] + "..."
            gas_used = int(tx.get("receipt_gas_used", 0))
            value_wei = int(tx.get("value", "0"))
            value_eth = value_wei / 1e18
            
            tx_summary = [
                f"\n{idx}. Transaction {tx_hash}",
                f"   Time: {time_str}",
                f"   Gas Used: {gas_used:,}",
                f"   Value: {value_eth:.6f} ETH",
                f"   Block: {safe_str(tx.get('block_number', 'Unknown'))}"
            ]
            
            summary.extend(tx_summary)
        
        if total_transactions > 5:
            summary.append(f"\n... and {total_transactions - 5} more transactions")
        
        # Add gas usage note for carbon calculation
        summary.append(f"\nCarbon Footprint Data:")
        summary.append(f"  Network: {chain.upper()}")
        summary.append(f"  Total Gas Consumed: {total_gas_used:,} units")
        summary.append(f"  Transaction Count: {total_transactions:,}")
        summary.append(f"  This data can be used to calculate carbon emissions based on network-specific emission factors.")
        
        return "\n".join(summary)