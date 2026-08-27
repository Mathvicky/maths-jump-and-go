#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage:"
  echo "  $0 <stack-name> <change-set-name>"
  exit 1
fi

STACK_NAME="$1"
CHANGE_SET_NAME="$2"
AWS_REGION="${AWS_REGION:-eu-west-2}"

aws cloudformation describe-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGE_SET_NAME}" \
  --region "${AWS_REGION}" \
  --include-property-values \
  --query \
'{Status:Status,Reason:StatusReason,Changes:Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Type:ResourceType,Replacement:Replacement}}' \
  --output json
