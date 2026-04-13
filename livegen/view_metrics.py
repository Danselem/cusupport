#!/usr/bin/env python3
"""Helper script to view metrics with conversation transcripts."""

import json
import sys
from datetime import datetime
from pathlib import Path


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return iso_str


def view_metrics_file(filepath: str) -> None:
    """Display metrics from a JSON file."""
    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        print(f"\n{'=' * 80}")
        print(f"📊 CALL METRICS - {Path(filepath).name}")
        print(f"{'=' * 80}\n")

        # Basic info
        print(f"Room ID:             {data.get('room_id', 'N/A')}")
        print(f"Duration:            {data.get('duration_seconds', 0):.1f} seconds")
        print(
            f"Consent:             {'✅ Given' if data.get('consent_obtained') else '❌ Denied'}"
        )
        print(
            f"Phone Collected:     {'✅ Yes' if data.get('phone_collected') else '❌ No'}"
        )
        print(f"Errors:              {data.get('error_count', 0)}")

        # Conversation transcript
        conversation = data.get("conversation", [])
        if conversation:
            print(f"\n{'=' * 80}")
            print(f"📝 CONVERSATION TRANSCRIPT ({len(conversation)} turns)")
            print(f"{'=' * 80}\n")

            for i, turn in enumerate(conversation, 1):
                timestamp = format_timestamp(turn.get("timestamp", ""))
                role = turn.get("role", "unknown").upper()
                message = turn.get("message", "")

                # Color code by role
                if role == "AGENT":
                    role_str = "🤖 AGENT"
                elif role == "USER":
                    role_str = "👤 USER"
                elif role == "SYSTEM":
                    role_str = "⚙️  SYSTEM"
                else:
                    role_str = f"❓ {role}"

                print(f"{i}. [{timestamp}] {role_str}:")
                print(f"   {message}")
                print()
        else:
            print("\n⚠️  No conversation recorded")

        print(f"{'=' * 80}\n")

    except Exception as e:
        print(f"❌ Error reading file: {e}")


def list_all_metrics() -> None:
    """List all available metrics files."""
    metrics_dir = Path("./metrics_data")

    if not metrics_dir.exists():
        print("❌ No metrics_data directory found")
        return

    files = sorted(metrics_dir.glob("**/*.json"))

    if not files:
        print("❌ No metrics files found")
        return

    print(f"\n{'=' * 80}")
    print(f"📊 AVAILABLE METRICS FILES ({len(files)} files)")
    print(f"{'=' * 80}\n")

    for i, filepath in enumerate(files, 1):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            room_id = data.get("room_id", "unknown")
            duration = data.get("duration_seconds", 0)
            has_conversation = len(data.get("conversation", [])) > 0

            print(f"{i}. {filepath.name}")
            print(
                f"   Room: {room_id} | Duration: {duration:.1f}s | Has Conversation: {'✅' if has_conversation else '❌'}"
            )
            print()
        except Exception as e:
            print(f"{i}. {filepath.name} (Error reading: {e})")
            print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # View specific file
        filepath = sys.argv[1]
        view_metrics_file(filepath)
    else:
        # List all metrics
        list_all_metrics()

        # Try to show the most recent one
        metrics_dir = Path("./metrics_data")
        files = sorted(metrics_dir.glob("**/*.json"))

        if files:
            print("\nTo view a specific call, run:")
            print(f"  python view_metrics.py {files[-1]}")


if __name__ == "__main__":
    main()
