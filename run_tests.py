"""
Unified test runner for display tests.
Modes: quick | comprehensive | status
"""
import asyncio
from comprehensive_display_test import run_comprehensive_display_test
from test_status import run_status_tests


async def run_display_tests(display_manager, mode="quick"):
    """
    Run display tests with the given mode.
    - quick: one game per sport, short run
    - comprehensive: all sports, statuses, edge cases, modes, transitions
    - status: status-label only (Rain Delay, Postponed, etc.)
    """
    if mode == "status":
        await run_status_tests(display_manager)
        return
    if mode in ("quick", "comprehensive"):
        await run_comprehensive_display_test(display_manager, mode)
        return
    print(f"Unknown test mode: {mode}. Use 'quick', 'comprehensive', or 'status'")
