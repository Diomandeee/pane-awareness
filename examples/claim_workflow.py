#!/usr/bin/env python3
"""Demonstrate the resource claiming lifecycle.

Shows: claim -> contest -> force_release -> re-claim
"""

import pane_awareness as pa


def main():
    # First, register our pane
    pa.update_pane(
        session_id="claim-demo",
        cwd="/home/user/project",
        prompt_text="working on the database migration",
    )

    # Claim a file resource
    print("=== Claiming file:src/models.py ===")
    result = pa.claim_resource(
        resource="file:src/models.py",
        scope="exclusive",
        reason="refactoring the User model",
    )
    print(f"  Result: {result}")

    # View active claims
    claims = pa.get_active_claims()
    print(f"\nActive claims: {len(claims.get('claims', []))}")
    for claim in claims.get("claims", []):
        print(f"  {claim.get('resource')} — held by {claim.get('holder_tty')}")
        print(f"    Scope: {claim.get('scope')}, Reason: {claim.get('reason')}")

    # Release the claim
    print("\n=== Releasing file:src/models.py ===")
    result = pa.release_resource("file:src/models.py")
    print(f"  Result: {result}")

    # View claims history
    log = pa.get_claims_log(limit=10)
    print(f"\nClaims log ({len(log)} entries):")
    for entry in log[-5:]:
        print(f"  [{entry.get('event')}] {entry.get('resource')} by {entry.get('holder_tty')}")


if __name__ == "__main__":
    main()
