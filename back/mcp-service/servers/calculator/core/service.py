"""
Calculator service core logic.
"""

import logging
import math
import statistics
import re
from typing import Any, Dict, List, Union
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.core_base import BaseService


logger = logging.getLogger(__name__)


class CalculatorService(BaseService):
    """Core service for calculator operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize calculator service."""
        super().__init__(config)
        
        # Safe mathematical functions for eval
        self.safe_functions = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "pow": pow,
            # Math module functions
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "atan2": math.atan2,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "ceil": math.ceil,
            "floor": math.floor,
            "factorial": math.factorial,
            "degrees": math.degrees,
            "radians": math.radians,
            "pi": math.pi,
            "e": math.e,
        }

        # Safe names for eval
        self.safe_names = {"__builtins__": {}, **self.safe_functions}
    
    async def health_check(self) -> bool:
        """Check if calculator service is healthy."""
        try:
            # Test a simple calculation
            result = self.safe_eval("2 + 2")
            return result == 4
        except Exception:
            return False
    
    def safe_eval(self, expression: str) -> Union[float, int]:
        """Safely evaluate a mathematical expression"""
        # Remove any potentially dangerous characters/keywords
        dangerous_patterns = [
            r"import\s+\w+",
            r"exec\s*\(",
            r"eval\s*\(",
            r"open\s*\(",
            r"file\s*\(",
            r"input\s*\(",
            r"raw_input\s*\(",
            r"__\w+__",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous expression: {expression}")

        # Only allow specific characters
        allowed_chars = set("0123456789+-*/().abcdefghijklmnopqrstuvwxyz_,[] ")
        if not all(c.lower() in allowed_chars for c in expression):
            raise ValueError(f"Invalid characters in expression: {expression}")

        # Evaluate the expression
        try:
            result = eval(expression, self.safe_names, {})
            return result
        except Exception as e:
            raise ValueError(f"Evaluation error: {str(e)}")

    async def calculate(self, expression: str, precision: int = 10) -> Dict[str, Any]:
        """Perform mathematical calculations.
        
        Args:
            expression: Mathematical expression to evaluate
            precision: Number of decimal places for the result
            
        Returns:
            Calculation result
        """
        try:
            self.logger.info(f"Calculating: {expression}")
            
            result = self.safe_eval(expression)

            # Round result if it's a float
            if isinstance(result, float):
                result = round(result, precision)

            self.logger.info(f"Calculation result: {result}")
            
            return {
                "success": True,
                "result": result,
                "expression": expression,
                "precision": precision,
                "formatted": f"Result: {result}\nExpression: {expression}"
            }
                
        except Exception as e:
            self.logger.error(f"Calculate error: {e}")
            raise Exception(f"Calculation failed: {str(e)}")

    async def calculate_statistics(self, data: List[float], operations: List[str] = None) -> Dict[str, Any]:
        """Calculate statistical measures for a dataset.
        
        Args:
            data: Array of numerical data points
            operations: Statistical operations to perform
            
        Returns:
            Statistical results
        """
        if operations is None:
            operations = ["mean", "median", "std"]
        
        try:
            self.logger.info(f"📊 Calculating statistics for {len(data)} data points")
            
            if not data:
                raise ValueError("No data provided")

            results = {}

            # Basic statistics
            if "count" in operations:
                results["count"] = len(data)

            if "sum" in operations:
                results["sum"] = sum(data)

            if "mean" in operations:
                results["mean"] = statistics.mean(data)

            if "median" in operations:
                results["median"] = statistics.median(data)

            if "mode" in operations:
                try:
                    results["mode"] = statistics.mode(data)
                except statistics.StatisticsError:
                    results["mode"] = "No unique mode"

            if "min" in operations:
                results["min"] = min(data)

            if "max" in operations:
                results["max"] = max(data)

            if "range" in operations:
                results["range"] = max(data) - min(data)

            # Advanced statistics (require at least 2 data points)
            if len(data) >= 2:
                if "std" in operations or "stdev" in operations:
                    results["stdev"] = statistics.stdev(data)

                if "var" in operations or "variance" in operations:
                    results["variance"] = statistics.variance(data)

            # Quantiles (require at least 4 data points)
            if len(data) >= 4:
                if "quartiles" in operations:
                    sorted_data = sorted(data)
                    results["quartiles"] = {
                        "q1": statistics.quantiles(sorted_data, n=4)[0],
                        "q2": statistics.median(sorted_data),
                        "q3": statistics.quantiles(sorted_data, n=4)[2],
                    }

            self.logger.info("✅ Statistics calculated successfully")
            
            stats_text = "Statistical Results:\n"
            for stat, value in results.items():
                if isinstance(value, dict):
                    stats_text += f"- {stat}:\n"
                    for k, v in value.items():
                        stats_text += f"  - {k}: {v}\n"
                else:
                    stats_text += f"- {stat}: {value}\n"
            stats_text += f"Data points: {len(data)}"
            
            return {
                "success": True,
                "results": results,
                "count": len(data),
                "formatted": stats_text
            }
                
        except Exception as e:
            self.logger.error(f"Statistics error: {e}")
            raise Exception(f"Statistics calculation failed: {str(e)}")

    async def convert_units(self, value: float, from_unit: str, to_unit: str, unit_type: str = "length") -> Dict[str, Any]:
        """Convert between different units of measurement.
        
        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
            unit_type: Type of unit conversion
            
        Returns:
            Conversion result
        """
        try:
            self.logger.info(f"🔄 Converting {value} {from_unit} to {to_unit}")

            # Conversion factors (to base unit)
            conversions = {
                "length": {
                    "mm": 0.001,
                    "cm": 0.01,
                    "m": 1.0,
                    "km": 1000.0,
                    "in": 0.0254,
                    "ft": 0.3048,
                    "yd": 0.9144,
                    "mi": 1609.34,
                },
                "weight": {
                    "mg": 0.000001,
                    "g": 0.001,
                    "kg": 1.0,
                    "oz": 0.0283495,
                    "lb": 0.453592,
                    "ton": 1000.0,
                },
            }

            if unit_type == "temperature":
                # Special temperature conversion logic
                celsius_value = value
                if from_unit.lower() == "f":
                    celsius_value = (value - 32) * 5 / 9
                elif from_unit.lower() == "k":
                    celsius_value = value - 273.15

                if to_unit.lower() == "c":
                    result = celsius_value
                elif to_unit.lower() == "f":
                    result = celsius_value * 9 / 5 + 32
                elif to_unit.lower() == "k":
                    result = celsius_value + 273.15
                else:
                    raise ValueError(f"Unknown temperature unit: {to_unit}")
            else:
                if unit_type not in conversions:
                    raise ValueError(f"Unknown unit type: {unit_type}")

                unit_map = conversions[unit_type]

                if from_unit not in unit_map:
                    raise ValueError(f"Unknown unit: {from_unit}")

                if to_unit not in unit_map:
                    raise ValueError(f"Unknown unit: {to_unit}")

                # Convert to base unit, then to target unit
                base_value = value * unit_map[from_unit]
                result = base_value / unit_map[to_unit]
            
            # Round result
            result = round(result, 6)
            
            self.logger.info(f"✅ Conversion result: {result}")
            
            formatted = f"Conversion Result: {value} {from_unit} = {result} {to_unit}"
            
            return {
                "success": True,
                "original_value": value,
                "converted_value": result,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "unit_type": unit_type,
                "formatted": formatted
            }
                
        except Exception as e:
            self.logger.error(f"Unit conversion error: {e}")
            raise Exception(f"Unit conversion failed: {str(e)}")

    async def list_math_functions(self) -> Dict[str, Any]:
        """Get available mathematical functions.
        
        Returns:
            Available functions
        """
        try:
            functions_data = {
                "basic_operations": {
                    "+": "Addition",
                    "-": "Subtraction", 
                    "*": "Multiplication",
                    "/": "Division",
                    "**": "Power/Exponentiation",
                    "%": "Modulo"
                },
                "mathematical_functions": {
                    "sqrt": "Square root",
                    "abs": "Absolute value",
                    "round": "Round to nearest integer",
                    "pow": "Power function",
                    "min": "Minimum value",
                    "max": "Maximum value",
                    "sum": "Sum of values"
                },
                "trigonometric": {
                    "sin": "Sine",
                    "cos": "Cosine", 
                    "tan": "Tangent",
                    "asin": "Arc sine",
                    "acos": "Arc cosine",
                    "atan": "Arc tangent"
                },
                "logarithmic": {
                    "log": "Natural logarithm",
                    "log10": "Base-10 logarithm",
                    "log2": "Base-2 logarithm",
                    "exp": "Exponential function"
                },
                "constants": {
                    "pi": "Pi (3.14159...)",
                    "e": "Euler's number (2.71828...)"
                },
                "statistics": {
                    "mean": "Average value",
                    "median": "Middle value",
                    "mode": "Most frequent value",
                    "std/stdev": "Standard deviation",
                    "var/variance": "Variance",
                    "min": "Minimum value",
                    "max": "Maximum value",
                    "quartiles": "Q1, Q2, Q3 values"
                }
            }
            
            functions_text = "Available Mathematical Functions:\n\n"
            
            for category, funcs in functions_data.items():
                functions_text += f"**{category.upper().replace('_', ' ')}:**\n"
                for func_name, func_desc in funcs.items():
                    functions_text += f"- {func_name}: {func_desc}\n"
                functions_text += "\n"
            
            return {
                "success": True,
                "functions": functions_data,
                "formatted": functions_text
            }
                
        except Exception as e:
            self.logger.error(f"List functions error: {e}")
            raise Exception(f"Failed to list functions: {str(e)}")
