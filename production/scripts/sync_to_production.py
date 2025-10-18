#!/usr/bin/env python3
"""
Sync Team Code to Production

This script syncs code from teams/ and shared/ directories to production/
for deployment to Render.

Usage:
    python production/scripts/sync_to_production.py <team-name>

Example:
    python production/scripts/sync_to_production.py golf-enrichment
"""

import sys
import shutil
from pathlib import Path


def sync_team_to_production(team_name: str) -> None:
    """
    Sync a team's code to production folder

    Args:
        team_name: Name of the team (e.g., 'golf-enrichment')
    """

    # Define paths
    repo_root = Path(__file__).parent.parent.parent
    team_dir = repo_root / "teams" / team_name
    shared_dir = repo_root / "shared"
    prod_dir = repo_root / "production" / team_name

    # Validation
    if not team_dir.exists():
        print(f"❌ Error: Team directory not found: {team_dir}")
        sys.exit(1)

    if not prod_dir.exists():
        print(f"❌ Error: Production directory not found: {prod_dir}")
        print(f"   Create it first with: mkdir -p production/{team_name}")
        sys.exit(1)

    print(f"🔄 Syncing {team_name} to production...")
    print(f"   Team: {team_dir}")
    print(f"   Shared: {shared_dir}")
    print(f"   Production: {prod_dir}")
    print()

    # 1. Sync team agents
    team_agents_src = team_dir / "agents"
    team_agents_dest = prod_dir / "agents"

    if team_agents_src.exists():
        # Clean destination
        if team_agents_dest.exists():
            shutil.rmtree(team_agents_dest)
        team_agents_dest.mkdir(parents=True)

        # Copy all agents
        for agent_file in team_agents_src.glob("*.py"):
            shutil.copy2(agent_file, team_agents_dest / agent_file.name)
            print(f"   ✓ Copied agent: {agent_file.name}")

    # 2. Sync orchestrator
    orchestrator_src = team_dir / "orchestrator.py"
    if orchestrator_src.exists():
        shutil.copy2(orchestrator_src, team_agents_dest / "orchestrator.py")
        print(f"   ✓ Copied orchestrator.py")

    # 3. Sync shared utilities
    shared_utils_src = shared_dir / "utils"
    shared_utils_dest = prod_dir / "template" / "utils"

    if shared_utils_src.exists():
        # Clean destination
        if shared_utils_dest.exists():
            shutil.rmtree(shared_utils_dest)
        shared_utils_dest.mkdir(parents=True)

        # Copy all utils
        for util_file in shared_utils_src.glob("*.py"):
            shutil.copy2(util_file, shared_utils_dest / util_file.name)
            print(f"   ✓ Copied util: {util_file.name}")

    # 4. Sync shared agents (if any exist in future)
    shared_agents_src = shared_dir / "agents"
    if shared_agents_src.exists() and any(shared_agents_src.glob("*.py")):
        for shared_agent in shared_agents_src.glob("*.py"):
            shutil.copy2(shared_agent, team_agents_dest / shared_agent.name)
            print(f"   ✓ Copied shared agent: {shared_agent.name}")

    # 5. Update requirements.txt (if team has custom requirements)
    team_reqs = team_dir / "requirements.txt"
    prod_reqs = prod_dir / "requirements.txt"
    if team_reqs.exists():
        shutil.copy2(team_reqs, prod_reqs)
        print(f"   ✓ Updated requirements.txt")

    print()
    print(f"✅ Sync complete! Production ready for deployment.")
    print(f"   Next steps:")
    print(f"   1. cd production/{team_name}")
    print(f"   2. Test locally: docker build -t {team_name}-test .")
    print(f"   3. git add production/{team_name}")
    print(f"   4. git commit -m 'Update {team_name} production code'")
    print(f"   5. git push (auto-deploys if render.yaml has autoDeploy: true)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python production/scripts/sync_to_production.py <team-name>")
        print("Example: python production/scripts/sync_to_production.py golf-enrichment")
        sys.exit(1)

    team_name = sys.argv[1]
    sync_team_to_production(team_name)
