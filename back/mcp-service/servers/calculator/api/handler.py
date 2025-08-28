"""
Calculator API handler.
"""

import logging
from typing import Any, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.api_base import BaseAPIHandler


logger = logging.getLogger(__name__)


class CalculatorAPIHandler(BaseAPIHandler):
    """API handler for calculator server."""
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for calculator server."""
        return {
            "calculate": {
                "description": "Perform mathematical calculations including basic arithmetic, advanced functions, and expressions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2+2', 'sin(3.14)', 'sqrt(16)')"
                        },
                        "precision": {
                            "type": "integer",
                            "description": "Number of decimal places for the result (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["expression"]
                }
            },
            "calculate_statistics": {
                "description": "Calculate statistical measures (mean, median, mode, standard deviation) for a dataset",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numerical data points"
                        },
                        "operations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Statistical operations to perform (mean, median, mode, std, var, min, max)",
                            "default": ["mean", "median", "std"]
                        }
                    },
                    "required": ["data"]
                }
            },
            "convert_units": {
                "description": "Convert between different units of measurement",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Value to convert"
                        },
                        "from_unit": {
                            "type": "string",
                            "description": "Source unit"
                        },
                        "to_unit": {
                            "type": "string",
                            "description": "Target unit"
                        },
                        "unit_type": {
                            "type": "string",
                            "description": "Type of unit conversion (length, weight, temperature, etc.)",
                            "default": "length"
                        }
                    },
                    "required": ["value", "from_unit", "to_unit"]
                }
            },
            "list_math_functions": {
                "description": "Get a list of available mathematical functions and their descriptions",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    async def handle_calculate(self, arguments: Dict[str, Any]) -> str:
        """Handle calculate tool call."""
        validated_args = self._validate_arguments(
            arguments, 
            required_args=["expression"],
            optional_args={"precision": 10}
        )
        
        try:
            result = await self.service.calculate(
                expression=validated_args["expression"],
                precision=validated_args["precision"]
            )
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Calculation error: {str(e)}")
    
    async def handle_calculate_statistics(self, arguments: Dict[str, Any]) -> str:
        """Handle calculate_statistics tool call."""
        validated_args = self._validate_arguments(
            arguments,
            required_args=["data"],
            optional_args={"operations": ["mean", "median", "std"]}
        )
        
        try:
            result = await self.service.calculate_statistics(
                data=validated_args["data"],
                operations=validated_args["operations"]
            )
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Statistics calculation error: {str(e)}")
    
    async def handle_convert_units(self, arguments: Dict[str, Any]) -> str:
        """Handle convert_units tool call."""
        validated_args = self._validate_arguments(
            arguments,
            required_args=["value", "from_unit", "to_unit"],
            optional_args={"unit_type": "length"}
        )
        
        try:
            result = await self.service.convert_units(
                value=validated_args["value"],
                from_unit=validated_args["from_unit"],
                to_unit=validated_args["to_unit"],
                unit_type=validated_args["unit_type"]
            )
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Unit conversion error: {str(e)}")
    
    async def handle_list_math_functions(self, arguments: Dict[str, Any]) -> str:
        """Handle list_math_functions tool call."""
        try:
            result = await self.service.list_math_functions()
            return result["formatted"]
        except Exception as e:
            raise Exception(f"Failed to list functions: {str(e)}")
