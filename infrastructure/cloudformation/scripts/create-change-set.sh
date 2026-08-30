#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage:"
  echo "  $0 <stack-name> <change-set-name> <template-file> <parameters-file>"
  exit 1
fi

STACK_NAME="$1"
CHANGE_SET_NAME="$2"
TEMPLATE_FILE="$3"
PARAMETERS_FILE="$4"
AWS_REGION="${AWS_REGION:-eu-west-2}"

if [[ ! -f "${TEMPLATE_FILE}" ]]; then
  echo "Template not found: ${TEMPLATE_FILE}"
  exit 1
fi

if [[ ! -f "${PARAMETERS_FILE}" ]]; then
  echo "Parameters not found: ${PARAMETERS_FILE}"
  exit 1
fi

CHANGE_SET_TYPE="CREATE"

if aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${AWS_REGION}" \
  >/dev/null 2>&1; then
  CHANGE_SET_TYPE="UPDATE"
fi

echo "Stack: ${STACK_NAME}"
echo "Change set: ${CHANGE_SET_NAME}"
echo "Type: ${CHANGE_SET_TYPE}"
echo "Region: ${AWS_REGION}"

aws cloudformation create-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGE_SET_NAME}" \
  --change-set-type "${CHANGE_SET_TYPE}" \
  --template-body "file://${TEMPLATE_FILE}" \
  --parameters "file://${PARAMETERS_FILE}" \
  --region "${AWS_REGION}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --description "Preview generated from the maths-jump-and-go repository"

echo "Waiting for CloudFormation to prepare the preview..."

if ! aws cloudformation wait change-set-create-complete \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGE_SET_NAME}" \
  --region "${AWS_REGION}"; then
  echo "Change-set creation did not complete successfully."

  aws cloudformation describe-change-set \
    --stack-name "${STACK_NAME}" \
    --change-set-name "${CHANGE_SET_NAME}" \
    --region "${AWS_REGION}" \
    --query '{Status:Status,Reason:StatusReason}' \
    --output table

  exit 1
fi

echo
echo "Proposed resource changes:"

aws cloudformation describe-change-set \
  --stack-name "${STACK_NAME}" \
  --change-set-name "${CHANGE_SET_NAME}" \
  --region "${AWS_REGION}" \
  --query \
'Changes[].ResourceChange.{Action:Action,LogicalId:LogicalResourceId,Type:ResourceType,Replacement:Replacement}' \
  --output table

echo
echo "Preview only. No AWS resources have been deployed."
echo "Review the change set before using the separate execution command."
