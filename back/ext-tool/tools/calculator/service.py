"""
Calculator Service
Business logic for mathematical operations and computational utilities
"""

import math
import statistics
import re
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel

from core.logging import get_logger

logger = get_logger(__name__)


class CalculationRequest(BaseModel):
    """Calculation request model"""

    expression: str
    precision: Optional[int] = 10


class CalculationResult(BaseModel):
    """Calculation result model"""

    expression: str
    result: Union[float, int, str]
    success: bool = True
    error: Optional[str] = None
    precision: int = 10


class StatisticsRequest(BaseModel):
    """Statistics calculation request"""

    data: List[Union[float, int]]
    operations: List[str] = ["mean", "median", "mode", "std", "var"]


class StatisticsResult(BaseModel):
    """Statistics calculation result"""

    data: List[Union[float, int]]
    results: Dict[str, Union[float, int, List[Union[float, int]]]]
    count: int
    success: bool = True
    error: Optional[str] = None


class CalculatorService:
    """Service for mathematical calculations"""

    def __init__(self):
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

    async def calculate(self, request: CalculationRequest) -> CalculationResult:
        """Perform mathematical calculation"""
        logger.info(f"Calculating: {request.expression}")

        try:
            result = self.safe_eval(request.expression)

            # Round result if it's a float
            if isinstance(result, float):
                result = round(result, request.precision)

            logger.info(f"Calculation result: {result}")

            return CalculationResult(
                expression=request.expression,
                result=result,
                success=True,
                precision=request.precision,
            )

        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return CalculationResult(
                expression=request.expression,
                result=str(e),
                success=False,
                error=str(e),
                precision=request.precision,
            )

    async def calculate_simple(
        self, expression: str, precision: int = 10
    ) -> CalculationResult:
        """Simple calculation with string expression"""
        request = CalculationRequest(expression=expression, precision=precision)
        return await self.calculate(request)

    async def calculate_statistics(
        self, request: StatisticsRequest
    ) -> StatisticsResult:
        """Calculate statistics for a dataset"""
        logger.info(f"📊 Calculating statistics for {len(request.data)} data points")

        try:
            if not request.data:
                raise ValueError("No data provided")

            results = {}

            # Basic statistics
            if "count" in request.operations:
                results["count"] = len(request.data)

            if "sum" in request.operations:
                results["sum"] = sum(request.data)

            if "mean" in request.operations:
                results["mean"] = statistics.mean(request.data)

            if "median" in request.operations:
                results["median"] = statistics.median(request.data)

            if "mode" in request.operations:
                try:
                    results["mode"] = statistics.mode(request.data)
                except statistics.StatisticsError:
                    results["mode"] = "No unique mode"

            if "min" in request.operations:
                results["min"] = min(request.data)

            if "max" in request.operations:
                results["max"] = max(request.data)

            if "range" in request.operations:
                results["range"] = max(request.data) - min(request.data)

            # Advanced statistics (require at least 2 data points)
            if len(request.data) >= 2:
                if "std" in request.operations or "stdev" in request.operations:
                    results["stdev"] = statistics.stdev(request.data)

                if "var" in request.operations or "variance" in request.operations:
                    results["variance"] = statistics.variance(request.data)

            # Quantiles (require at least 4 data points)
            if len(request.data) >= 4:
                if "quartiles" in request.operations:
                    sorted_data = sorted(request.data)
                    results["quartiles"] = {
                        "q1": statistics.quantiles(sorted_data, n=4)[0],
                        "q2": statistics.median(sorted_data),
                        "q3": statistics.quantiles(sorted_data, n=4)[2],
                    }

            logger.info("✅ Statistics calculated successfully")

            return StatisticsResult(
                data=request.data,
                results=results,
                count=len(request.data),
                success=True,
            )

        except Exception as e:
            logger.error(f"Statistics calculation error: {e}")
            return StatisticsResult(
                data=request.data,
                results={},
                count=len(request.data) if request.data else 0,
                success=False,
                error=str(e),
            )

    def list_functions(self) -> Dict[str, Any]:
        """List available mathematical functions"""
        return {
            "basic_operations": ["+", "-", "*", "/", "**", "%"],
            "functions": list(self.safe_functions.keys()),
            "constants": ["pi", "e"],
            "statistics": [
                "mean",
                "median",
                "mode",
                "std",
                "var",
                "min",
                "max",
                "sum",
                "count",
                "range",
                "quartiles",
            ],
            "examples": [
                "2 + 3 * 4",
                "sqrt(16)",
                "sin(pi/2)",
                "log(e)",
                "factorial(5)",
                "pow(2, 8)",
            ],
        }

    async def convert_units(
        self, value: float, from_unit: str, to_unit: str, unit_type: str = "length"
    ) -> Dict[str, Any]:
        """Convert between units"""
        logger.info(f"🔄 Converting {value} {from_unit} to {to_unit}")

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

        try:
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

            logger.info(f"✅ Conversion result: {result}")

            return {
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": round(result, 6),
                "converted_unit": to_unit,
                "unit_type": unit_type,
                "success": True,
            }

        except Exception as e:
            logger.error(f"❌ Conversion error: {e}")
            raise Exception(str(e))
