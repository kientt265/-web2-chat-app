#!/usr/bin/env python3
"""
Calculator MCP Server

An MCP server that provides mathematical calculation tools.
This is part of the MCP microservice.
"""

import logging
from typing import Any
import os

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator-mcp-server")

# Calculator service URL (configured via environment or default)
EXT_TOOL_SERVICE_URL = os.getenv("EXT_TOOL_SERVICE_URL", "http://ext-tool:3006")
CALCULATOR_SERVICE_URL = f"{EXT_TOOL_SERVICE_URL}/tools/calculator"

# Create FastMCP app
app = FastMCP("calculator")


@app.tool()
def calculate(expression: str, precision: int = 10) -> str:
    """Perform mathematical calculations including basic arithmetic, advanced functions, and expressions.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., '2+2', 'sin(3.14)', 'sqrt(16)')
        precision: Number of decimal places for the result (default: 10)
    
    Returns:
        String containing the calculation result
    """
    try:
        import asyncio
        
        async def _calculate():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{CALCULATOR_SERVICE_URL}/calculate",
                    json={
                        "expression": expression,
                        "precision": precision
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("success", False):
                    return f"Result: {result['result']}\nExpression: {result['expression']}"
                else:
                    return f"Calculation Error: {result.get('error', 'Unknown error')}"
        
        # Run async function
        return asyncio.run(_calculate())
        
    except Exception as e:
        logger.error(f"Calculate error: {e}")
        return f"Error performing calculation: {str(e)}"


@app.tool()
def calculate_statistics(data: list[float], operations: list[str] = None) -> str:
    """Calculate statistical measures (mean, median, mode, standard deviation) for a dataset.
    
    Args:
        data: Array of numerical data points
        operations: Statistical operations to perform (mean, median, mode, std, var, min, max)
    
    Returns:
        String containing statistical results
    """
    if operations is None:
        operations = ["mean", "median", "std"]
    
    try:
        import asyncio
        
        async def _calculate_stats():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{CALCULATOR_SERVICE_URL}/statistics",
                    json={
                        "data": data,
                        "operations": operations
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("success", False):
                    stats_text = "Statistical Results:\n"
                    for stat, value in result.get("results", {}).items():
                        stats_text += f"- {stat}: {value}\n"
                    stats_text += f"Data points: {result.get('count', 0)}"
                    return stats_text
                else:
                    return f"Statistics Error: {result.get('error', 'Unknown error')}"
        
        return asyncio.run(_calculate_stats())
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        return f"Error calculating statistics: {str(e)}"


@app.tool()
def convert_units(value: float, from_unit: str, to_unit: str, unit_type: str = "length") -> str:
    """Convert between different units of measurement.
    
    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit
        unit_type: Type of unit conversion (length, weight, temperature, etc.)
    
    Returns:
        String containing conversion result
    """
    try:
        import asyncio
        
        async def _convert():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{CALCULATOR_SERVICE_URL}/convert",
                    params={
                        "value": value,
                        "from_unit": from_unit,
                        "to_unit": to_unit,
                        "unit_type": unit_type
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                return f"Conversion Result: {value} {from_unit} = {result.get('result', 'N/A')} {to_unit}"
        
        return asyncio.run(_convert())
        
    except Exception as e:
        logger.error(f"Unit conversion error: {e}")
        return f"Error converting units: {str(e)}"


@app.tool()
def list_math_functions() -> str:
    """Get a list of available mathematical functions and their descriptions.
    
    Returns:
        String containing available mathematical functions
    """
    try:
        import asyncio
        
        async def _list_functions():
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{CALCULATOR_SERVICE_URL}/functions")
                response.raise_for_status()
                result = response.json()
                
                functions_text = "Available Mathematical Functions:\n\n"
                
                for category, funcs in result.get("functions", {}).items():
                    functions_text += f"**{category.upper()}:**\n"
                    for func_name, func_desc in funcs.items():
                        functions_text += f"- {func_name}: {func_desc}\n"
                    functions_text += "\n"
                
                return functions_text
        
        return asyncio.run(_list_functions())
        
    except Exception as e:
        logger.error(f"List functions error: {e}")
        return f"Error listing functions: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting Calculator MCP Server")
    # This will be managed by the MCP service, not run directly
    app.run(transport='sse', port=8001)
