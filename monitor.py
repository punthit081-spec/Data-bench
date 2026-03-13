#!/usr/bin/env python3
"""Defensive domain breach monitor.

This script is intentionally limited for blue-team usage:
- Accepts a URL
- Extracts and normalizes domain
- Queries allowed intelligence connectors
- Aggregates risk summary and recommendations
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass
class Incident:
    source: str
    title: str
    affected_domain: str
    leaked_fields: list[str]
    severity: str
    first_seen: str
    reference: str


class Connector:
    name: str

    def fetch(self, domain: str) -> list[Incident]:
        raise NotImplementedError


class DemoFileConnector(Connector):
    def __init__(self, path: str):
        self.name = "demo_file"
        self.path = path

    def fetch(self, domain: str) -> list[Incident]:
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        incidents: list[Incident] = []
        for item in payload:
            if item.get("affected_domain", "").lower() != domain:
                continue
            incidents.append(
                Incident(
                    source=self.name,
                    title=item["title"],
                    affected_domain=item["affected_domain"].lower(),
                    leaked_fields=item.get("leaked_fields", []),
                    severity=item.get("severity", "low").lower(),
                    first_seen=item.get("first_seen", "unknown"),
                    reference=item.get("reference", ""),
                )
            )
        return incidents


class HibpDomainConnector(Connector):
    """Optional connector for Have I Been Pwned domain API.

    This endpoint requires proper domain ownership verification and a valid API key.
    See HIBP docs for current endpoint/contract.
    """

    def __init__(self, api_key: str):
        self.name = "hibp_domain"
        self.api_key = api_key

    def fetch(self, domain: str) -> list[Incident]:
        endpoint = f"https://haveibeenpwned.com/api/v3/breacheddomain/{domain}"
        req = Request(
            endpoint,
            headers={
                "hibp-api-key": self.api_key,
                "user-agent": "data-bench-defensive-monitor/1.0",
            },
        )

        try:
            with urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
        except Exception:
            # Fail safely to avoid blocking full run on one source.
            return []

        incidents: list[Incident] = []
        for b in data if isinstance(data, list) else []:
            incidents.append(
                Incident(
                    source=self.name,
                    title=b.get("Name", "Unknown breach"),
                    affected_domain=domain,
                    leaked_fields=b.get("DataClasses", []),
                    severity="medium",
                    first_seen=b.get("BreachDate", "unknown"),
                    reference=b.get("Domain", ""),
                )
            )
        return incidents


def normalize_domain(raw_url: str) -> str:
    candidate = raw_url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower().strip(".")
    if not host:
        raise ValueError("Unable to parse domain from URL")
    return host


def pick_max_severity(incidents: list[Incident]) -> str:
    if not incidents:
        return "none"
    return max(incidents, key=lambda x: SEVERITY_ORDER.get(x.severity, 0)).severity


def recommendations(max_severity: str, has_incident: bool) -> list[str]:
    base = [
        "Verify ownership before querying any external source.",
        "Enable SPF/DKIM/DMARC and enforce strong password + MFA.",
        "Prepare user notification and forced credential reset workflow.",
    ]
    if not has_incident:
        return ["No breach records found from configured sources.", *base]
    if max_severity in {"high", "critical"}:
        return [
            "Start incident response immediately (IR bridge + timeline).",
            "Force reset credentials and rotate tokens/keys.",
            "Run threat hunting for credential-stuffing and suspicious logins.",
            *base,
        ]
    return ["Review incidents and prioritize remediation by exposed data type.", *base]


def run(url: str, connectors: list[Connector]) -> dict[str, Any]:
    domain = normalize_domain(url)
    all_incidents: list[Incident] = []
    per_source: dict[str, int] = {}

    for connector in connectors:
        rows = connector.fetch(domain)
        per_source[connector.name] = len(rows)
        all_incidents.extend(rows)

    max_sev = pick_max_severity(all_incidents)

    return {
        "target_domain": domain,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_incidents": len(all_incidents),
        "max_severity": max_sev,
        "sources": per_source,
        "incidents": [incident.__dict__ for incident in all_incidents],
        "recommendations": recommendations(max_sev, has_incident=bool(all_incidents)),
        "note": "For defensive/authorized monitoring only.",
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Defensive domain breach monitor")
    p.add_argument("--url", required=True, help="Target URL or domain")
    p.add_argument(
        "--demo-data",
        default="data/demo_breaches.json",
        help="Path to demo JSON feed",
    )
    p.add_argument(
        "--enable-hibp",
        action="store_true",
        help="Enable HIBP Domain connector (requires HIBP_API_KEY)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    connectors: list[Connector] = [DemoFileConnector(args.demo_data)]

    if args.enable_hibp:
        api_key = os.environ.get("HIBP_API_KEY")
        if not api_key:
            print("ERROR: --enable-hibp needs HIBP_API_KEY", file=sys.stderr)
            return 2
        connectors.append(HibpDomainConnector(api_key))

    output = run(args.url, connectors)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
