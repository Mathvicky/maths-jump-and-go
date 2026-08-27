# Math's Jump & Go Infrastructure

Production-style AWS and Kubernetes infrastructure for the Math's Jump & Go platform.

## Infrastructure as Code

AWS resources will be provisioned with AWS CloudFormation.

## Planned AWS components

- Amazon VPC
- Public and private subnets across Availability Zones
- Internet Gateway and controlled outbound networking
- Amazon ECR
- Amazon EKS
- IAM roles and GitHub Actions OIDC federation
- Application Load Balancer
- Route 53 and ACM HTTPS certificates
- AWS Secrets Manager or Systems Manager Parameter Store
- Amazon CloudWatch logs, metrics, dashboards and alarms

## Kubernetes platform

- Namespaces
- Deployment
- ClusterIP Service
- Ingress
- ConfigMap and Secret integration
- Resource requests and limits
- Liveness, readiness and startup probes
- Horizontal Pod Autoscaler
- Pod disruption controls
- RBAC
- Network policies
- Helm chart
- Argo CD or Flux GitOps delivery

## CI pipeline

- Source validation
- Backend tests
- CloudFormation validation
- Docker image build
- Dependency and image security scans
- Container registry publishing
- Immutable image tagging

## CD pipeline

- Infrastructure plan and controlled deployment
- GitOps configuration update
- EKS deployment through Helm
- Health and smoke tests
- Environment approval gates
- Rollback and recovery procedures

## Security principles

- No permanent AWS keys in GitHub
- GitHub OIDC with short-lived AWS credentials
- Least-privilege IAM
- Private workload networking
- Encrypted configuration
- HTTPS for public traffic
- Security scanning before deployment
- Audit-friendly Git history

## AWS region

Primary region: eu-west-2
