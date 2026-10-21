output "ecr_repositories" { value = { for k, r in aws_ecr_repository.svc : k => r.repository_url } }
output "github_ci_role_arn" { value = aws_iam_role.github_ci.arn }
output "eks_cluster_name" { value = try(module.eks[0].cluster_name, null) }
