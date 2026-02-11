#!/bin/sh
set -e

DOCS_USER="${DOCS_USER:-panbot}"
DOCS_PASSWORD="${DOCS_PASSWORD:-changeme}"

htpasswd -cb /etc/nginx/.htpasswd "$DOCS_USER" "$DOCS_PASSWORD"
