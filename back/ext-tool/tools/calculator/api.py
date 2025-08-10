"""
Calculator Tool API
HTTP endpoints for mathematical operations and computational utilities
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any, Union

from core.logging import get_logger
from .service import CalculatorService, CalculationRequest, CalculationResult, StatisticsRequest, StatisticsResult

router = APIRouter()
logger = get_logger(__name__)

# Global service instance
calc_service = CalculatorService()


@router.post("/calculate", response_model=CalculationResult)
async def calculate(request: CalculationRequest):
    """Perform mathematical calculation"""
    try:
        result = await calc_service.calculate(request)
        return result
    except Exception as e:
        logger.error(f"❌ Calculation error: {e}")
        return CalculationResult(
            expression=request.expression,
            result=str(e),
            success=False,
            error=str(e),
            precision=request.precision
        )


@router.get("/calculate")
async def calculate_simple(
    expression: str,
    precision: int = 10
):
    """Simple calculation endpoint"""
    try:
        result = await calc_service.calculate_simple(expression, precision)
        return result
    except Exception as e:
        logger.error(f"❌ Simple calculation error: {e}")
        return CalculationResult(
            expression=expression,
            result=str(e),
            success=False,
            error=str(e),
            precision=precision
        )


@router.post("/statistics", response_model=StatisticsResult)
async def calculate_statistics(request: StatisticsRequest):
    """Calculate statistics for a dataset"""
    try:
        result = await calc_service.calculate_statistics(request)
        return result
    except Exception as e:
        logger.error(f"❌ Statistics error: {e}")
        return StatisticsResult(
            data=request.data,
            results={},
            count=len(request.data) if request.data else 0,
            success=False,
            error=str(e)
        )


@router.get("/functions")
async def list_functions():
    """List available mathematical functions"""
    return calc_service.list_functions()


@router.get("/convert")
async def unit_conversion(
    value: float,
    from_unit: str,
    to_unit: str,
    unit_type: str = "length"
):
    """Convert between units"""
    try:
        result = await calc_service.convert_units(value, from_unit, to_unit, unit_type)
        return result
    except Exception as e:
        logger.error(f"❌ Conversion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health")
async def calculator_health():
    """Health check for calculator tool"""
    functions = calc_service.list_functions()
    return {
        "status": "healthy",
        "capabilities": ["basic_math", "advanced_math", "statistics", "unit_conversion"],
        "functions_count": len(functions.get("functions", []))
    }
