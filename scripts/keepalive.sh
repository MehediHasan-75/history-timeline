#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${APP_HEALTH_URL:-}" ]]; then
  echo "APP_HEALTH_URL is required" >&2
  exit 2
fi
curl --fail --silent --show-error --location --retry 3 --retry-all-errors --connect-timeout 10 --max-time 90 "${APP_HEALTH_URL%/}/health/live/"
