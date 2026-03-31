#!/usr/bin/env python3
"""Open the AWS Management Console using credentials from .env.

Uses the AWS federation endpoint to generate a sign-in URL from
temporary credentials (access key + secret key + session token).

Usage: uv run tests/aws_console.py
       uv run tests/aws_console.py --service s3
       uv run tests/aws_console.py --service s3 --region us-west-2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

FEDERATION_URL = "https://signin.aws.amazon.com/federation"
CONSOLE_URL = "https://console.aws.amazon.com/"


def get_signin_url(destination: str) -> str:
    """Generate a federated AWS Console sign-in URL."""
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    session_token = os.environ.get("AWS_SESSION_TOKEN")

    if not all([access_key, secret_key, session_token]):
        print(
            "Error: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and "
            "AWS_SESSION_TOKEN must all be set in .env.\n"
            "This script requires temporary credentials (e.g., from "
            "AWS SSO, STS AssumeRole, or similar).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 1: Get a sign-in token from the federation endpoint
    session_json = json.dumps({
        "sessionId": access_key,
        "sessionKey": secret_key,
        "sessionToken": session_token,
    })

    token_params = urllib.parse.urlencode({
        "Action": "getSigninToken",
        "SessionDuration": "3600",
        "Session": session_json,
    })

    token_url = f"{FEDERATION_URL}?{token_params}"
    req = urllib.request.Request(token_url)
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read().decode("utf-8"))

    signin_token = token_data.get("SigninToken")
    if not signin_token:
        print(
            f"Error: Failed to get sign-in token: {token_data}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 2: Build the console login URL
    login_params = urllib.parse.urlencode({
        "Action": "login",
        "Issuer": "deep-research-agent",
        "Destination": destination,
        "SigninToken": signin_token,
    })

    return f"{FEDERATION_URL}?{login_params}"


def build_destination(service: str | None, region: str | None) -> str:
    """Build the console destination URL for a given service."""
    region = (
        region
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )

    if not service:
        return f"{CONSOLE_URL}?region={region}"

    service_urls = {
        "s3": f"https://s3.console.aws.amazon.com/s3/buckets?region={region}",
        "bedrock": f"https://{region}.console.aws.amazon.com/bedrock/home?region={region}",
        "cloudwatch": f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}",
        "iam": "https://us-east-1.console.aws.amazon.com/iam/home",
        "lambda": f"https://{region}.console.aws.amazon.com/lambda/home?region={region}",
        "sagemaker": f"https://{region}.console.aws.amazon.com/sagemaker/home?region={region}",
    }

    return service_urls.get(
        service.lower(),
        f"https://{region}.console.aws.amazon.com/{service}/home?region={region}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Open AWS Console using .env credentials"
    )
    parser.add_argument(
        "--service", "-s",
        help="AWS service to open (e.g., s3, bedrock, cloudwatch)",
    )
    parser.add_argument(
        "--region", "-r",
        help="AWS region (defaults to AWS_REGION from .env)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Print URL instead of opening browser",
    )
    args = parser.parse_args()

    destination = build_destination(args.service, args.region)
    print(f"Destination: {destination}")
    print("Generating sign-in URL...")

    url = get_signin_url(destination)

    print(f"\nConsole URL:\n{url}")

    if not args.no_open:
        print("\nOpening browser...")
        webbrowser.open(url)


if __name__ == "__main__":
    main()
