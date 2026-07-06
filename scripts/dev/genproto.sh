#!/usr/bin/env bash
# Regenerate Python protobuf stubs from proto/ into agents/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

python -m grpc_tools.protoc \
  -I proto \
  --python_out=agents \
  --pyi_out=agents \
  proto/dualmind/v1/event.proto

# protoc does not emit package inits; create them so imports are explicit.
touch agents/dualmind/__init__.py agents/dualmind/v1/__init__.py

echo "Generated stubs under agents/dualmind/"
