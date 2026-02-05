"""Tests for code generator fixes."""
from generators.base import MAX_CHILDREN_LIMIT, MAX_NATIVE_CHILDREN_LIMIT


class TestChildLimitsConsistency:
    """Verify child limits are consistent across modules."""

    def test_web_child_limit_is_20(self):
        assert MAX_CHILDREN_LIMIT == 20

    def test_native_child_limit_is_15(self):
        assert MAX_NATIVE_CHILDREN_LIMIT == 15

    def test_figma_mcp_imports_from_base(self):
        """figma_mcp.py should import limits from base.py, not define its own."""
        import importlib.util
        import inspect
        # Read figma_mcp.py source
        with open('figma_mcp.py', 'r') as f:
            source = f.read()
        # Should NOT have standalone MAX_CHILDREN_LIMIT = <number> assignment
        import re
        standalone_defs = re.findall(r'^MAX_CHILDREN_LIMIT\s*=\s*\d+', source, re.MULTILINE)
        assert len(standalone_defs) == 0, f"figma_mcp.py still defines its own MAX_CHILDREN_LIMIT: {standalone_defs}"
