"""AgentScope CLI main entry point."""

import argparse
import sys
from .commands import (
    setup_cmd, status_cmd, uninstall_cmd,
    pricing_list_cmd, pricing_set_cmd, pricing_remove_cmd, pricing_calc_cmd,
)


def create_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="agentscope",
        description="AgentScope - Setup and management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agentscope setup nanobot --workspace ~/.nanobot
  agentscope setup nanobot --workspace ~/.nanobot-zhangjuzheng --name zhangjuzheng
  agentscope status
  agentscope uninstall nanobot --workspace ~/.nanobot

Pricing commands:
  agentscope pricing list              # List all model pricing
  agentscope pricing set gpt-4 0.03 0.06  # Set pricing for a model
  agentscope pricing calc -m gpt-4 -i 1000 -o 500  # Calculate cost
  agentscope pricing remove my-model   # Remove a model's pricing
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Setup AgentScope monitoring for an agent framework",
    )
    setup_parser.add_argument(
        "framework",
        choices=["nanobot", "agentscope", "custom"],
        help="Agent framework to setup",
    )
    setup_parser.add_argument(
        "--workspace",
        "-w",
        required=True,
        help="Path to the agent workspace directory",
    )
    setup_parser.add_argument(
        "--name",
        "-n",
        help="Instance name (for multi-instance setups)",
    )
    setup_parser.add_argument(
        "--backend",
        "-b",
        default="http://localhost:8000",
        help="AgentScope backend URL (default: http://localhost:8000)",
    )
    setup_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing configuration",
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check AgentScope status",
    )
    status_parser.add_argument(
        "--backend",
        "-b",
        default="http://localhost:8000",
        help="AgentScope backend URL",
    )
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Remove AgentScope monitoring from an agent framework",
    )
    uninstall_parser.add_argument(
        "framework",
        choices=["nanobot", "agentscope", "custom"],
        help="Agent framework to uninstall",
    )
    uninstall_parser.add_argument(
        "--workspace",
        "-w",
        required=True,
        help="Path to the agent workspace directory",
    )
    
    # Pricing command
    pricing_parser = subparsers.add_parser(
        "pricing",
        help="Manage token pricing configuration",
    )
    pricing_subparsers = pricing_parser.add_subparsers(
        dest="pricing_command",
        help="Pricing subcommands",
    )
    
    # pricing list
    pricing_list_parser = pricing_subparsers.add_parser(
        "list",
        help="List all model pricing",
    )
    
    # pricing set
    pricing_set_parser = pricing_subparsers.add_parser(
        "set",
        help="Set pricing for a model",
    )
    pricing_set_parser.add_argument("model", help="Model name")
    pricing_set_parser.add_argument("input_price", type=float, help="Input price per 1K tokens (USD)")
    pricing_set_parser.add_argument("output_price", type=float, help="Output price per 1K tokens (USD)")
    pricing_set_parser.add_argument(
        "--currency", "-c",
        default="USD",
        help="Currency code (default: USD)",
    )
    
    # pricing remove
    pricing_remove_parser = pricing_subparsers.add_parser(
        "remove",
        help="Remove pricing for a model",
    )
    pricing_remove_parser.add_argument("model", help="Model name to remove")
    
    # pricing calc
    pricing_calc_parser = pricing_subparsers.add_parser(
        "calc",
        help="Calculate cost for token usage",
    )
    pricing_calc_parser.add_argument(
        "--model", "-m",
        default="default",
        help="Model name (default: default)",
    )
    pricing_calc_parser.add_argument(
        "--input-tokens", "-i",
        type=int,
        default=1000,
        help="Number of input tokens (default: 1000)",
    )
    pricing_calc_parser.add_argument(
        "--output-tokens", "-o",
        type=int,
        default=500,
        help="Number of output tokens (default: 500)",
    )
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "setup":
            setup_cmd(args)
        elif args.command == "status":
            status_cmd(args)
        elif args.command == "uninstall":
            uninstall_cmd(args)
        elif args.command == "pricing":
            if not args.pricing_command:
                pricing_parser = [p for p in parser._subparsers._actions if hasattr(p, 'choices') and 'pricing' in str(p.choices)][0]
                pricing_parser.choices['pricing'].print_help()
                sys.exit(1)
            elif args.pricing_command == "list":
                pricing_list_cmd(args)
            elif args.pricing_command == "set":
                pricing_set_cmd(args)
            elif args.pricing_command == "remove":
                pricing_remove_cmd(args)
            elif args.pricing_command == "calc":
                pricing_calc_cmd(args)
    except KeyboardInterrupt:
        print("\n✋ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
