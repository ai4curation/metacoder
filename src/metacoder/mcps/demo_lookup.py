#!/usr/bin/env python3
"""Demo MCP server with lookup_id tool for testing."""

from fastmcp import FastMCP

mcp = FastMCP("ACME store Lookup Service")


@mcp.tool
def lookup_id(n: int) -> str:
    """Look up an ID in ACME store and return the name of the corresponding product
    
    Args:
        n: The identifier of the entity to look up
        
    Returns:
        Name of the product
    """
    if n % 2 == 0:
        return "salt and vinegar potato chips"
    else:
        return "chocolate chip cookies"

def main():
    mcp.run()

if __name__ == "__main__":
    main()