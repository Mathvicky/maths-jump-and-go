#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TEMPLATES_DIR="${ROOT_DIR}/infrastructure/cloudformation/templates"
PARAMETERS_DIR="${ROOT_DIR}/infrastructure/cloudformation/parameters"
AWS_REGION="${AWS_REGION:-eu-west-2}"

echo "Validating CloudFormation templates with cfn-lint..."

find "${TEMPLATES_DIR}" \
  -type f \
  \( -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) \
  -print0 |
while IFS= read -r -d '' template; do
  echo "Linting: ${template#${ROOT_DIR}/}"
  cfn-lint --template "${template}" --region "${AWS_REGION}"
done

echo "Validating parameter JSON files..."

find "${PARAMETERS_DIR}" \
  -type f \
  -name "*.json" \
  -print0 |
while IFS= read -r -d '' parameters; do
  echo "Checking: ${parameters#${ROOT_DIR}/}"
  python -m json.tool "${parameters}" >/dev/null
done

echo "CloudFormation validation passed."
