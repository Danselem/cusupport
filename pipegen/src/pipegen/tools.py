"""Tools for function calling in the agent."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class Tool:
    """Represents a callable tool/function."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_list(self) -> list[dict[str, Any]]:
        """Get list of tools in OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        try:
            result = tool.handler(**arguments)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            raise


# Sample tools for customer service


def get_customer_info(customer_id: str) -> dict[str, Any]:
    """Get customer information by ID."""
    # In production, this would query a database
    return {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "account_type": "Premium",
        "member_since": "2023-01-15",
    }


def lookup_order(order_id: str) -> dict[str, Any]:
    """Look up order details by order ID."""
    # In production, this would query an order system
    return {
        "order_id": order_id,
        "status": "shipped",
        "items": [
            {"name": "Widget Pro", "quantity": 2, "price": 49.99},
        ],
        "total": 99.98,
        "shipping_address": "123 Main St, Anytown, USA",
        "estimated_delivery": "2026-04-10",
    }


def create_support_ticket(
    customer_id: str,
    subject: str,
    description: str,
    priority: str = "normal",
) -> dict[str, Any]:
    """Create a support ticket."""
    # In production, this would create a ticket in a ticketing system
    ticket_id = f"TICKET-{hash((customer_id, subject)) % 10000:04d}"
    return {
        "ticket_id": ticket_id,
        "status": "open",
        "subject": subject,
        "description": description,
        "priority": priority,
        "created_at": "2026-04-04T12:00:00Z",
    }


def get_product_info(product_name: str) -> dict[str, Any]:
    """Get product information by name."""
    # In production, this would query a product catalog
    products = {
        "widget pro": {
            "name": "Widget Pro",
            "description": "Professional-grade widget with advanced features",
            "price": 49.99,
            "in_stock": True,
            "sku": "WGT-PRO-001",
        },
        "widget basic": {
            "name": "Widget Basic",
            "description": "Essential widget for everyday use",
            "price": 19.99,
            "in_stock": True,
            "sku": "WGT-BSC-001",
        },
    }

    product = products.get(product_name.lower())
    if not product:
        return {"error": f"Product not found: {product_name}"}
    return product


def get_default_tools() -> list[Tool]:
    """Get the default set of tools for customer service."""
    return [
        Tool(
            name="get_customer_info",
            description="Get customer information by their customer ID",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's unique identifier",
                    },
                },
                "required": ["customer_id"],
            },
            handler=get_customer_info,
        ),
        Tool(
            name="lookup_order",
            description="Look up order status and details using order ID",
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order's unique identifier",
                    },
                },
                "required": ["order_id"],
            },
            handler=lookup_order,
        ),
        Tool(
            name="create_support_ticket",
            description="Create a support ticket for customer issues",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's unique identifier",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Brief subject of the issue",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Priority level of the ticket",
                    },
                },
                "required": ["customer_id", "subject", "description"],
            },
            handler=create_support_ticket,
        ),
        Tool(
            name="get_product_info",
            description="Get information about products in the catalog",
            parameters={
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product to look up",
                    },
                },
                "required": ["product_name"],
            },
            handler=get_product_info,
        ),
    ]


# Global registry instance
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        for tool in get_default_tools():
            _tool_registry.register(tool)
    return _tool_registry
