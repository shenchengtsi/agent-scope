"""Token pricing configuration with hot-reload support.

This module provides:
1. File-based pricing configuration (YAML/JSON)
2. Hot-reload on file changes
3. API for dynamic price updates
4. Backward compatibility with code-defined prices

Usage:
    # pricing.yaml
    models:
      gpt-4:
        input: 0.03    # $ per 1K tokens
        output: 0.06
      kimi-for-coding:
        input: 0.0004
        output: 0.0021
    
    # Python
    from agentscope.pricing import get_pricing, calculate_cost
    cost = calculate_cost(input_tokens=1000, output_tokens=500, model="gpt-4")
"""

import os
import json
import yaml
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Default pricing (fallback when no config file exists)
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "default": {"input": 0.0015, "output": 0.002},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "kimi-for-coding": {"input": 0.0004, "output": 0.0021},
    "kimi": {"input": 0.0004, "output": 0.0021},
    "MiniMax-M2.7": {"input": 0.00021, "output": 0.00084},
    "minimax": {"input": 0.00021, "output": 0.00084},
}


@dataclass
class ModelPricing:
    """Pricing for a single model."""
    input: float   # $ per 1K input tokens
    output: float  # $ per 1K output tokens
    currency: str = "USD"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ModelPricing":
        return cls(
            input=float(data.get("input", 0)),
            output=float(data.get("output", 0)),
            currency=data.get("currency", "USD")
        )


class PricingManager:
    """Manages token pricing with hot-reload support."""
    
    def __init__(self, config_path: Optional[str] = None):
        self._pricing: Dict[str, ModelPricing] = {}
        self._config_path: Optional[Path] = None
        self._last_modified: float = 0
        self._last_check: float = 0
        self._check_interval: float = 5.0  # Check every 5 seconds
        self._lock = threading.RLock()
        self._on_reload_callbacks: list = []
        
        # Load default pricing
        self._load_defaults()
        
        # Set config path
        if config_path:
            self._config_path = Path(config_path)
        else:
            # Default locations: ~/.agentscope/pricing.yaml or pricing.json
            home = Path.home()
            agentscope_dir = home / ".agentscope"
            if (agentscope_dir / "pricing.yaml").exists():
                self._config_path = agentscope_dir / "pricing.yaml"
            elif (agentscope_dir / "pricing.json").exists():
                self._config_path = agentscope_dir / "pricing.json"
        
        # Initial load from file if exists
        if self._config_path and self._config_path.exists():
            self._load_from_file()
        
        # Start hot-reload watcher
        self._start_watcher()
    
    def _load_defaults(self):
        """Load default pricing."""
        with self._lock:
            for model, prices in DEFAULT_PRICING.items():
                self._pricing[model] = ModelPricing(
                    input=prices["input"],
                    output=prices["output"]
                )
    
    def _load_from_file(self) -> bool:
        """Load pricing from config file. Returns True if successful."""
        if not self._config_path or not self._config_path.exists():
            return False
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                if self._config_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            if not data or "models" not in data:
                logger.warning(f"Invalid pricing config: {self._config_path}")
                return False
            
            with self._lock:
                # Update pricing from file (overrides defaults)
                for model_name, prices in data["models"].items():
                    self._pricing[model_name] = ModelPricing.from_dict(prices)
                
                # Update last modified time
                stat = self._config_path.stat()
                self._last_modified = stat.st_mtime
            
            logger.info(f"Loaded pricing config from {self._config_path}: {len(data['models'])} models")
            self._notify_reload()
            return True
            
        except Exception as e:
            logger.error(f"Failed to load pricing config: {e}")
            return False
    
    def _save_to_file(self) -> bool:
        """Save current pricing to config file. Returns True if successful."""
        if not self._config_path:
            # Create default path
            agentscope_dir = Path.home() / ".agentscope"
            agentscope_dir.mkdir(exist_ok=True)
            self._config_path = agentscope_dir / "pricing.yaml"
        
        try:
            with self._lock:
                data = {
                    "version": "1.0",
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "models": {
                        name: pricing.to_dict()
                        for name, pricing in self._pricing.items()
                        if name != "default" or len(self._pricing) == 1
                    }
                }
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                if self._config_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._last_modified = self._config_path.stat().st_mtime
            logger.info(f"Saved pricing config to {self._config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save pricing config: {e}")
            return False
    
    def _check_reload(self):
        """Check if config file has been modified and reload if necessary."""
        if not self._config_path or not self._config_path.exists():
            return
        
        now = time.time()
        # Throttle checks
        if now - self._last_check < self._check_interval:
            return
        self._last_check = now
        
        try:
            stat = self._config_path.stat()
            if stat.st_mtime > self._last_modified:
                logger.info(f"Pricing config changed, reloading...")
                self._load_from_file()
        except Exception as e:
            logger.error(f"Error checking config file: {e}")
    
    def _start_watcher(self):
        """Start background thread for hot-reload."""
        def watcher_loop():
            while True:
                time.sleep(self._check_interval)
                self._check_reload()
        
        thread = threading.Thread(target=watcher_loop, daemon=True, name="pricing-watcher")
        thread.start()
        logger.debug("Started pricing config watcher")
    
    def _notify_reload(self):
        """Notify callbacks that pricing has been reloaded."""
        for callback in self._on_reload_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in reload callback: {e}")
    
    def on_reload(self, callback: Callable):
        """Register a callback to be called when pricing is reloaded."""
        self._on_reload_callbacks.append(callback)
    
    def get(self, model: str) -> ModelPricing:
        """Get pricing for a model. Returns default if not found."""
        self._check_reload()
        with self._lock:
            return self._pricing.get(model, self._pricing.get("default"))
    
    def get_all(self) -> Dict[str, ModelPricing]:
        """Get all pricing configurations."""
        self._check_reload()
        with self._lock:
            return dict(self._pricing)
    
    def set(self, model: str, input_price: float, output_price: float, 
            currency: str = "USD", persist: bool = True):
        """Set pricing for a model.
        
        Args:
            model: Model name
            input_price: Price per 1K input tokens in USD
            output_price: Price per 1K output tokens in USD
            currency: Currency code (default: USD)
            persist: Whether to save to config file (default: True)
        """
        with self._lock:
            self._pricing[model] = ModelPricing(
                input=input_price,
                output=output_price,
                currency=currency
            )
        
        if persist:
            self._save_to_file()
        
        logger.info(f"Set pricing for {model}: input=${input_price}/1K, output=${output_price}/1K")
    
    def remove(self, model: str, persist: bool = True):
        """Remove pricing for a model."""
        with self._lock:
            if model in self._pricing:
                del self._pricing[model]
        
        if persist:
            self._save_to_file()
        
        logger.info(f"Removed pricing for {model}")
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, 
                       model: str = "default") -> float:
        """Calculate cost for given token usage."""
        pricing = self.get(model)
        input_cost = (input_tokens / 1000) * pricing.input
        output_cost = (output_tokens / 1000) * pricing.output
        return input_cost + output_cost
    
    def get_config_path(self) -> Optional[Path]:
        """Get the current config file path."""
        return self._config_path
    
    def create_default_config(self, path: Optional[str] = None) -> str:
        """Create a default pricing config file.
        
        Returns:
            Path to created config file
        """
        if path:
            self._config_path = Path(path)
        elif not self._config_path:
            agentscope_dir = Path.home() / ".agentscope"
            agentscope_dir.mkdir(exist_ok=True)
            self._config_path = agentscope_dir / "pricing.yaml"
        
        self._save_to_file()
        return str(self._config_path)


# Global pricing manager instance
_pricing_manager: Optional[PricingManager] = None


def init_pricing(config_path: Optional[str] = None) -> PricingManager:
    """Initialize the pricing manager.
    
    Args:
        config_path: Path to pricing config file (YAML or JSON)
                    If None, uses ~/.agentscope/pricing.yaml
    
    Returns:
        PricingManager instance
    """
    global _pricing_manager
    _pricing_manager = PricingManager(config_path)
    return _pricing_manager


def get_pricing_manager() -> PricingManager:
    """Get the global pricing manager instance."""
    global _pricing_manager
    if _pricing_manager is None:
        _pricing_manager = PricingManager()
    return _pricing_manager


# Convenience functions
def get_pricing(model: str) -> Dict[str, float]:
    """Get pricing for a model."""
    pm = get_pricing_manager()
    p = pm.get(model)
    return {"input": p.input, "output": p.output, "currency": p.currency}


def set_pricing(model: str, input_price: float, output_price: float, 
                currency: str = "USD", persist: bool = True):
    """Set pricing for a model."""
    pm = get_pricing_manager()
    pm.set(model, input_price, output_price, currency, persist)


def calculate_cost(input_tokens: int, output_tokens: int, 
                   model: str = "default") -> float:
    """Calculate cost for given token usage."""
    pm = get_pricing_manager()
    return pm.calculate_cost(input_tokens, output_tokens, model)


def list_models() -> Dict[str, Dict[str, float]]:
    """List all configured models and their pricing."""
    pm = get_pricing_manager()
    return {name: {"input": p.input, "output": p.output, "currency": p.currency}
            for name, p in pm.get_all().items()}


def create_config(path: Optional[str] = None) -> str:
    """Create a default pricing config file."""
    pm = get_pricing_manager()
    return pm.create_default_config(path)
