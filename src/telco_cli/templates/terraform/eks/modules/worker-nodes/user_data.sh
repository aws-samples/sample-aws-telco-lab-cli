MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="==BOUNDARY=="

--==BOUNDARY==
Content-Type: application/node.eks.aws

---
apiVersion: node.eks.aws/v1alpha1
kind: NodeConfig
spec:
  cluster:
    apiServerEndpoint: ${cluster_endpoint}
    certificateAuthority: ${cluster_ca_cert}
    cidr: 10.100.0.0/16
    name: ${cluster_name}
  kubelet:
    config:
      clusterDNS:
      - 10.100.0.10
      # SJC38 specific kubelet configuration
      cpuManagerPolicy: "static"
      systemReservedCgroup: ""
      kubeReservedCgroup: ""
      topologyManagerPolicy: "single-numa-node"
      podPidsLimit: 4096
      systemReserved:
        memory: 1Gi
      kubeReserved:
        memory: 1Gi
      cpuManagerReconcilePeriod: 10s
      topologyManagerScope: pod
      allowedUnsafeSysctls:
      - "net.core.somaxconn"
      - "net.ipv4.ip_local_port_range"
      - "net.core.rmem_max"
      - "net.core.wmem_max"
      - "net.ipv4.tcp_rmem"
      - "net.ipv4.tcp_wmem"
      - "net.netfilter.nf_conntrack_max"
      - "net.netfilter.nf_conntrack_tcp_timeout_established"
      - "net.ipv4.neigh.default.gc_thresh1"
      - "net.ipv4.neigh.default.gc_thresh2"
      - "net.ipv4.neigh.default.gc_thresh3"
      - "kernel.shm_rmid_forced"
      - "net.ipv4.ip_forward"
      - "net.ipv6.conf.all.forwarding"
    flags:
    - --node-labels=node.longhorn.io/create-default-disk=true,storage=longhorn,is_worker=true,node-type=worker

--==BOUNDARY==
Content-Type: text/x-shellscript

#!/bin/bash
set -o xtrace

echo "Starting worker node initialization..."

# Configuration for storage (optimized for both regular and metal instances)
echo "Configuring storage for worker node..."

# List all NVMe devices for debugging
echo "Available NVMe devices:"
lsblk | grep nvme || echo "No NVMe devices found"

# Configure primary NVMe device for Longhorn if available
DEV_PATH="/dev/nvme1n1"
MOUNT_PATH="/mnt/longhorn"
FILESYSTEM_TYPE="xfs"

if [ -e "$DEV_PATH" ] && [ -b "$DEV_PATH" ]; then
    echo "Configuring $DEV_PATH for Longhorn storage..."
    
    # Create filesystem, mount point, and add to fstab
    if mkfs -t "$FILESYSTEM_TYPE" "$DEV_PATH"; then
        mkdir -p "$MOUNT_PATH"
        if mount "$DEV_PATH" "$MOUNT_PATH"; then
            echo "$DEV_PATH $MOUNT_PATH $FILESYSTEM_TYPE defaults,nofail 0 2" >> /etc/fstab
            echo "Longhorn storage device configured successfully"
        else
            echo "Warning: Failed to mount $DEV_PATH"
        fi
    else
        echo "Warning: Failed to create filesystem on $DEV_PATH"
    fi
else
    echo "Note: Primary NVMe device $DEV_PATH not found"
fi

echo "Worker node initialization completed"

--==BOUNDARY==--
