"""AgentScope CLI main entry point."""

import argparse
import sys
from .commands import setup_cmd, status_cmd, uninstall_cmd


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
    except KeyboardInterrupt:
        print("\n✋ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
