terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.0"
    }
  }
}

resource "helm_release" "outposts_bundle" {
  name       = "aws-cse-eks-addons-outposts-bundle"
  repository = "oci://public.ecr.aws/h1z9a8h6/awscse"
  chart      = "aws-cse-eks-addons-outposts-bundle"
  version    = "0.1.0"
  namespace  = "kube-system"

  values = [
    yamlencode({
      longhorn = {
        enabled = true
        defaultSettings = {
          guaranteedInstanceManagerCPU = 2
          nodeDownPodDeletionPolicy    = "delete-both-statefulset-and-deployment-pod"
        }
      }
      multus = {
        enabled = true
      }
      whereabouts = {
        enabled = true
      }
      sriovdp = {
        enabled = true
        resourceList = var.enable_sriov_discovery ? local.sriov_resource_list : [
          {
            resourceName = "intel_sriov_netdevice"
            selectors = {
              vendors = ["8086"]
              devices = ["154c", "10ed"]
              drivers = ["i40evf", "ixgbevf"]
            }
          }
        ]
      }
      sriovcni = {
        enabled = true
      }
    })
  ]

  depends_on = [var.cluster_endpoint]
}
