from typing import Type, Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
from pathlib import Path


class CarbonFootprintToolInput(BaseModel):
    """Input schema for Carbon Footprint Analysis Tool."""
    transaction_count: int = Field(..., description="Total number of transactions")
    network_distribution: Dict[str, int] = Field(..., description="Dictionary of network names to transaction counts")
    transaction_types: Dict[str, int] = Field(default_factory=dict, description="Dictionary of transaction types to counts")


class CarbonFootprintTool(BaseTool):
    """Tool to calculate carbon footprint from blockchain transactions."""
    name: str = "Carbon Footprint Calculator"
    description: str = (
        "Calculates the carbon footprint and energy consumption of blockchain transactions "
        "across multiple networks. Provides emission data in kg CO2 and kWh, and suggests "
        "strategies for carbon reduction. Use this to assess environmental impact of wallet activity."
    )
    args_schema: Type[BaseModel] = CarbonFootprintToolInput
    
    def __init__(self):
        """Initialize the CarbonFootprintTool."""
        super().__init__()
        self._carbon_data = self._load_carbon_data()
    
    def _load_carbon_data(self) -> Dict[str, Any]:
        """Load carbon emission data from JSON file."""
        try:
            # Try multiple possible paths for the carbon data file
            possible_paths = [
                Path(__file__).parent.parent / "data" / "carbon_data.json",
                Path("onchain_agent/data/carbon_data.json"),
                Path("data/carbon_data.json"),
                Path("carbon_data.json")
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r') as f:
                        return json.load(f)
            
            # If file not found, return default data
            return self._get_default_carbon_data()
        except Exception as e:
            print(f"Warning: Could not load carbon data: {e}. Using defaults.")
            return self._get_default_carbon_data()
    
    def _get_default_carbon_data(self) -> Dict[str, Any]:
        """Return default carbon data if JSON file is not available."""
        return {
            "networks": {
                "ethereum": {"co2_per_transaction_kg": 0.0001, "energy_per_transaction_kwh": 0.0002},
                "polygon": {"co2_per_transaction_kg": 0.00009, "energy_per_transaction_kwh": 0.00018},
                "optimism": {"co2_per_transaction_kg": 0.00005, "energy_per_transaction_kwh": 0.0001},
                "arbitrum": {"co2_per_transaction_kg": 0.00005, "energy_per_transaction_kwh": 0.0001},
                "base": {"co2_per_transaction_kg": 0.00005, "energy_per_transaction_kwh": 0.0001},
                "bsc": {"co2_per_transaction_kg": 0.00012, "energy_per_transaction_kwh": 0.00024},
                "avalanche": {"co2_per_transaction_kg": 0.0001, "energy_per_transaction_kwh": 0.0002}
            },
            "transaction_types": {
                "simple_transfer": {"multiplier": 1.0},
                "swap": {"multiplier": 1.5},
                "liquidity_add": {"multiplier": 2.0},
                "liquidity_remove": {"multiplier": 2.0},
                "nft_mint": {"multiplier": 2.5},
                "nft_transfer": {"multiplier": 1.2},
                "contract_deployment": {"multiplier": 5.0},
                "complex_defi": {"multiplier": 3.0}
            }
        }
    
    def _run(self, transaction_count: int, network_distribution: Dict[str, int], 
             transaction_types: Dict[str, int] = None) -> str:
        """Calculate carbon footprint based on transaction data."""
        try:
            if transaction_count == 0:
                return self._format_no_transactions()
            
            # Calculate emissions by network
            total_co2_kg = 0.0
            total_energy_kwh = 0.0
            network_emissions = {}
            
            for network, count in network_distribution.items():
                network_key = network.lower().replace(" ", "_").replace("-", "_")
                
                # Get network data or use default
                network_data = self._carbon_data["networks"].get(
                    network_key,
                    {"co2_per_transaction_kg": 0.0001, "energy_per_transaction_kwh": 0.0002}
                )
                
                # Calculate base emissions
                co2 = count * network_data["co2_per_transaction_kg"]
                energy = count * network_data["energy_per_transaction_kwh"]
                
                # Apply transaction type multipliers if available
                if transaction_types:
                    type_multiplier = self._calculate_type_multiplier(transaction_types, count)
                    co2 *= type_multiplier
                    energy *= type_multiplier
                
                network_emissions[network] = {
                    "transactions": count,
                    "co2_kg": co2,
                    "energy_kwh": energy
                }
                
                total_co2_kg += co2
                total_energy_kwh += energy
            
            # Calculate equivalent metrics
            equivalents = self._calculate_equivalents(total_co2_kg, total_energy_kwh)
            
            # Generate reduction strategies
            strategies = self._generate_strategies(network_distribution, total_co2_kg)
            
            # Format the response
            return self._format_carbon_report(
                transaction_count,
                total_co2_kg,
                total_energy_kwh,
                network_emissions,
                equivalents,
                strategies
            )
            
        except Exception as e:
            return f"Error calculating carbon footprint: {str(e)}"
    
    def _calculate_type_multiplier(self, transaction_types: Dict[str, int], total_count: int) -> float:
        """Calculate weighted average multiplier based on transaction types."""
        if not transaction_types or total_count == 0:
            return 1.0
        
        weighted_sum = 0.0
        for tx_type, count in transaction_types.items():
            type_key = tx_type.lower().replace(" ", "_")
            type_data = self._carbon_data["transaction_types"].get(
                type_key,
                {"multiplier": 1.0}
            )
            weighted_sum += count * type_data["multiplier"]
        
        return weighted_sum / total_count
    
    def _calculate_equivalents(self, co2_kg: float, energy_kwh: float) -> Dict[str, float]:
        """Calculate equivalent metrics for context."""
        return {
            "trees_needed_year": co2_kg / 21.77,  # Average tree absorbs ~21.77 kg CO2/year
            "km_driven": co2_kg / 0.12,  # Average car emits ~0.12 kg CO2/km
            "smartphone_charges": energy_kwh / 0.015,  # Average smartphone charge ~0.015 kWh
            "led_bulb_hours": energy_kwh / 0.01  # 10W LED bulb
        }
    
    def _generate_strategies(self, network_distribution: Dict[str, int], total_co2: float) -> List[Dict[str, Any]]:
        """Generate carbon reduction strategies based on transaction patterns."""
        strategies = []
        
        # Check if using high-emission networks
        high_emission_networks = ["ethereum", "bsc", "avalanche"]
        using_high_emission = any(net.lower() in high_emission_networks for net in network_distribution.keys())
        
        if using_high_emission:
            l2_potential = total_co2 * 0.5  # 50% reduction potential
            strategies.append({
                "name": "Migrate to Layer 2 Networks",
                "potential_reduction_kg": l2_potential,
                "reduction_percent": 50,
                "description": "Use L2 networks like Optimism, Arbitrum, or Base for transactions",
                "priority": "high"
            })
        
        # Batch transactions strategy
        if len(network_distribution) > 0:
            batch_potential = total_co2 * 0.3  # 30% reduction potential
            strategies.append({
                "name": "Batch Multiple Transactions",
                "potential_reduction_kg": batch_potential,
                "reduction_percent": 30,
                "description": "Combine multiple operations into single transactions when possible",
                "priority": "medium"
            })
        
        # Carbon offset strategy
        offset_cost = (total_co2 / 1000) * 15  # $15 per ton
        strategies.append({
            "name": "Purchase Carbon Offsets",
            "cost_usd": offset_cost,
            "description": "Offset emissions through verified carbon credit programs",
            "priority": "medium"
        })
        
        # Gas optimization
        gas_potential = total_co2 * 0.2  # 20% reduction potential
        strategies.append({
            "name": "Optimize Gas Usage",
            "potential_reduction_kg": gas_potential,
            "reduction_percent": 20,
            "description": "Use gas-efficient contracts and optimal transaction timing",
            "priority": "low"
        })
        
        return strategies
    
    def _format_no_transactions(self) -> str:
        """Format response when no transactions are found."""
        return """
# Carbon Footprint Analysis

## Summary
No transaction history found for this wallet. Carbon footprint cannot be calculated.

## Note
This wallet may be:
- A new wallet with no activity
- A holding wallet with minimal transactions
- Using networks not currently tracked

Environmental impact is minimal to zero based on available data.
"""
    
    def _format_carbon_report(self, tx_count: int, co2_kg: float, energy_kwh: float,
                              network_emissions: Dict, equivalents: Dict, strategies: List) -> str:
        """Format the complete carbon footprint report."""
        # Format network breakdown
        network_lines = []
        for network, data in sorted(network_emissions.items(), key=lambda x: x[1]['co2_kg'], reverse=True):
            network_lines.append(
                f"  - {network.title()}: {data['transactions']:,} txs → "
                f"{data['co2_kg']:.4f} kg CO2, {data['energy_kwh']:.4f} kWh"
            )
        
        # Format strategies
        strategy_lines = []
        for idx, strategy in enumerate(strategies, 1):
            strategy_lines.append(f"\n{idx}. **{strategy['name']}** (Priority: {strategy['priority'].upper()})")
            strategy_lines.append(f"   - {strategy['description']}")
            if 'potential_reduction_kg' in strategy:
                strategy_lines.append(
                    f"   - Potential Reduction: {strategy['potential_reduction_kg']:.4f} kg CO2 "
                    f"({strategy['reduction_percent']}%)"
                )
            if 'cost_usd' in strategy:
                strategy_lines.append(f"   - Estimated Cost: ${strategy['cost_usd']:.2f}")
        
        report = f"""
# Carbon Footprint Analysis

## Summary
- **Total Transactions Analyzed**: {tx_count:,}
- **Total CO2 Emissions**: {co2_kg:.4f} kg ({co2_kg/1000:.6f} metric tons)
- **Total Energy Consumed**: {energy_kwh:.4f} kWh

## Environmental Context
Your blockchain activity is equivalent to:
- 🌳 **{equivalents['trees_needed_year']:.2f}** trees needed for 1 year to offset
- 🚗 **{equivalents['km_driven']:.2f}** km driven in an average car
- 📱 **{equivalents['smartphone_charges']:.0f}** smartphone charges
- 💡 **{equivalents['led_bulb_hours']:.0f}** hours of LED bulb usage

## Emissions by Network
{chr(10).join(network_lines)}

## Carbon Reduction Strategies
{''.join(strategy_lines)}

## Overall Assessment
{"Your carbon footprint is relatively low due to minimal transaction activity." if co2_kg < 0.1 else 
 "Your carbon footprint is moderate. Consider implementing L2 migration strategies." if co2_kg < 1.0 else
 "Your carbon footprint is significant. Implementing reduction strategies could substantially lower your environmental impact."}

---
*Data based on post-merge Ethereum (Proof of Stake) and current network emission factors.*
"""
        return report.strip()