"""Unit tests for DescribeOutpostCommand."""

from argparse import Namespace
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from telco_cli.commands.describe_outpost import DescribeOutpostCommand


class TestDescribeOutpostCommand:
    """Test cases for DescribeOutpostCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = DescribeOutpostCommand()
        self.mock_args = Namespace(
            outpost_id="op-123456789",
            include_capacity=False,
            include_hosts=False,
            include_instances=False,
        )

    def test_command_properties(self):
        """Test command name and description."""
        assert self.command.name == "describe-outpost"
        assert "Get detailed information about a specific Outpost" in self.command.description

    @patch("telco_cli.commands.describe_outpost.boto3.client")
    def test_describe_outpost_success(self, mock_boto3):
        """Test successful outpost description."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        # Mock get_outpost response
        mock_outposts_client.get_outpost.return_value = {
            "Outpost": {
                "OutpostId": "op-123456789",
                "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                "Name": "TestOutpost",
                "Description": "Test outpost description",
                "LifeCycleStatus": "ACTIVE",
                "AvailabilityZone": "us-west-2a",
                "AvailabilityZoneId": "usw2-az1",
                "SiteId": "os-123456789",
                "SiteArn": "arn:aws:outposts:us-west-2:123456789012:site/os-123456789",
                "SupportedHardwareType": "RACK",
                "Tags": [{"Key": "Environment", "Value": "Test"}],
            }
        }

        # Mock get_site response
        mock_outposts_client.get_site.return_value = {
            "Site": {
                "Name": "TestSite",
                "Description": "Test site description",
                "Country": "US",
                "State": "WA",
                "City": "Seattle",
                "Address": {"AddressLine1": "123 Test St"},
                "Tags": [],
            }
        }

        result = self.command._describe_outpost(self.mock_args)

        assert result["Success"] is True
        assert result["Outpost"]["OutpostId"] == "op-123456789"
        assert result["Outpost"]["Name"] == "TestOutpost"
        assert result["Outpost"]["SiteDetails"]["Name"] == "TestSite"
        assert "LastUpdated" in result

    @patch("telco_cli.commands.describe_outpost.boto3.client")
    def test_describe_outpost_not_found(self, mock_boto3):
        """Test outpost not found error."""
        mock_outposts_client = Mock()
        mock_boto3.return_value = mock_outposts_client

        # Mock NotFoundException
        mock_outposts_client.get_outpost.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Outpost not found"}}, "GetOutpost"
        )

        result = self.command._describe_outpost(self.mock_args)

        assert result["Success"] is False
        assert result["Error"]["Code"] == "OutpostNotFound"
        assert "op-123456789 not found" in result["Error"]["Message"]

    @patch("telco_cli.commands.describe_outpost.boto3.client")
    def test_describe_outpost_with_capacity(self, mock_boto3):
        """Test outpost description with capacity information."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        self.mock_args.include_capacity = True

        # Mock basic outpost response
        mock_outposts_client.get_outpost.return_value = {
            "Outpost": {
                "OutpostId": "op-123456789",
                "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                "Name": "TestOutpost",
                "LifeCycleStatus": "ACTIVE",
                "AvailabilityZone": "us-west-2a",
                "SiteId": "os-123456789",
                "Tags": [],
            }
        }

        # Mock site response
        mock_outposts_client.get_site.return_value = {"Site": {"Name": "TestSite", "Tags": []}}

        # Mock instance types response
        mock_outposts_client.get_outpost_instance_types.return_value = {
            "InstanceTypes": [
                {"InstanceType": "m5.large"},
                {"InstanceType": "c5.xlarge"},
                {"InstanceType": "r5.2xlarge"},
            ]
        }

        result = self.command._describe_outpost(self.mock_args)

        assert result["Success"] is True
        assert "CapacityDetails" in result["Outpost"]
        assert result["Outpost"]["CapacityDetails"]["TotalInstanceTypes"] == 3
        assert "m5.large" in result["Outpost"]["CapacityDetails"]["ByCategory"]["GeneralPurpose"]
        assert "c5.xlarge" in result["Outpost"]["CapacityDetails"]["ByCategory"]["ComputeOptimized"]
        assert "r5.2xlarge" in result["Outpost"]["CapacityDetails"]["ByCategory"]["MemoryOptimized"]

    @patch("telco_cli.commands.describe_outpost.boto3.client")
    def test_describe_outpost_with_hosts(self, mock_boto3):
        """Test outpost description with physical assets information."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        self.mock_args.include_hosts = True

        # Mock basic outpost response
        mock_outposts_client.get_outpost.return_value = {
            "Outpost": {
                "OutpostId": "op-123456789",
                "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                "Name": "TestOutpost",
                "LifeCycleStatus": "ACTIVE",
                "AvailabilityZone": "us-west-2a",
                "SiteId": "os-123456789",
                "Tags": [],
            }
        }

        # Mock site response
        mock_outposts_client.get_site.return_value = {"Site": {"Name": "TestSite", "Tags": []}}

        # Mock list_assets response (AWS Outposts API)
        mock_outposts_client.list_assets.return_value = {
            "Assets": [
                {
                    "AssetId": "4005440408",
                    "RackId": "1703842924",
                    "AssetType": "COMPUTE",
                    "ComputeAttributes": {
                        "HostId": "h-123",
                        "State": "ACTIVE",
                        "InstanceFamilies": ["Bmn-cx2"],
                        "MaxVcpus": 192,
                        "InstanceTypeCapacities": [],
                    },
                    "AssetLocation": {"RackElevation": 31.0},
                },
                {
                    "AssetId": "4005440458",
                    "RackId": "1703842924",
                    "AssetType": "COMPUTE",
                    "ComputeAttributes": {
                        "HostId": "h-456",
                        "State": "ACTIVE",
                        "InstanceFamilies": ["Bmn-cx2"],
                        "MaxVcpus": 192,
                        "InstanceTypeCapacities": [],
                    },
                    "AssetLocation": {"RackElevation": 14.0},
                },
            ]
        }

        result = self.command._describe_outpost(self.mock_args)

        assert result["Success"] is True
        assert "PhysicalAssets" in result["Outpost"]
        assets_info = result["Outpost"]["PhysicalAssets"]
        assert assets_info["TotalAssets"] == 2
        assert assets_info["TotalVcpus"] == 384  # 192 * 2
        assert assets_info["ByState"]["ACTIVE"] == 2
        assert assets_info["ByInstanceFamily"]["Bmn-cx2"] == 2
        assert len(assets_info["AssetDetails"]) == 2
        assert assets_info["AssetDetails"][0]["AssetId"] == "4005440408"
        assert assets_info["AssetDetails"][0]["RackElevation"] == 31.0

    @patch("subprocess.run")
    def test_describe_outpost_with_instances(self, mock_subprocess):
        """Test outpost description with instances information."""
        self.mock_args.include_instances = True

        # Mock subprocess response for list-asset-instances
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"AssetInstances": [{"InstanceId": "i-123", "InstanceType": "bmn-cx2.metal-48xl", "AssetId": "4005440408", "AccountId": "123456789012"}]}'
        mock_subprocess.return_value = mock_result

        result = self.command._get_outpost_instances_details("op-123456789")

        assert "TotalInstances" in result
        assert result["TotalInstances"] == 1
        assert "ByInstanceType" in result
        assert result["ByInstanceType"]["bmn-cx2.metal-48xl"] == 1
        assert "ByAccount" in result
        assert result["ByAccount"]["123456789012"] == 1
        assert len(result["InstanceDetails"]) == 1
        assert result["InstanceDetails"][0]["InstanceId"] == "i-123"

    def test_get_outpost_capacity_details_categorization(self):
        """Test instance type categorization in _get_outpost_capacity_details."""
        mock_outposts_client = Mock()
        mock_outposts_client.get_outpost_instance_types.return_value = {
            "InstanceTypes": [
                {"InstanceType": "m5.large"},  # General purpose
                {"InstanceType": "c5.xlarge"},  # Compute optimized
                {"InstanceType": "r5.2xlarge"},  # Memory optimized
                {"InstanceType": "d3.4xlarge"},  # Storage optimized
                {"InstanceType": "p3.8xlarge"},  # Accelerated computing
                {"InstanceType": "t3.medium"},  # General purpose
            ]
        }

        result = self.command._get_outpost_capacity_details(mock_outposts_client, "op-123")

        assert result["TotalInstanceTypes"] == 6
        assert "m5.large" in result["ByCategory"]["GeneralPurpose"]
        assert "t3.medium" in result["ByCategory"]["GeneralPurpose"]
        assert "c5.xlarge" in result["ByCategory"]["ComputeOptimized"]
        assert "r5.2xlarge" in result["ByCategory"]["MemoryOptimized"]
        assert "d3.4xlarge" in result["ByCategory"]["StorageOptimized"]
        assert "p3.8xlarge" in result["ByCategory"]["AcceleratedComputing"]

    def test_get_outpost_capacity_details_error(self):
        """Test error handling in _get_outpost_capacity_details."""
        mock_outposts_client = Mock()
        mock_outposts_client.get_outpost_instance_types.side_effect = Exception("API Error")

        result = self.command._get_outpost_capacity_details(mock_outposts_client, "op-123")

        assert "Error" in result
        assert "API Error" in result["Error"]

    def test_get_outpost_hosts_details_no_assets(self):
        """Test _get_outpost_hosts_details with no assets."""
        mock_outposts_client = Mock()
        mock_outposts_client.list_assets.return_value = {"Assets": []}

        result = self.command._get_outpost_hosts_details(mock_outposts_client, "op-123")

        assert result["TotalAssets"] == 0
        assert "Message" in result
        assert "No compute assets found" in result["Message"]

    def test_get_outpost_hosts_details_error(self):
        """Test error handling in _get_outpost_hosts_details."""
        mock_outposts_client = Mock()
        mock_outposts_client.list_assets.side_effect = Exception("API Error")

        result = self.command._get_outpost_hosts_details(mock_outposts_client, "op-123")

        assert "Error" in result
        assert "API Error" in result["Error"]

    @patch("subprocess.run")
    def test_get_outpost_instances_details_error(self, mock_subprocess):
        """Test error handling in _get_outpost_instances_details."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Access denied"
        mock_subprocess.return_value = mock_result

        result = self.command._get_outpost_instances_details("op-123")

        assert "Error" in result
        assert "Access denied" in result["Error"]

    @patch("telco_cli.commands.describe_outpost.boto3.client")
    def test_describe_outpost_aws_error(self, mock_boto3):
        """Test AWS error handling."""
        mock_outposts_client = Mock()
        mock_boto3.return_value = mock_outposts_client

        # Mock generic ClientError
        mock_outposts_client.get_outpost.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "GetOutpost"
        )

        result = self.command._describe_outpost(self.mock_args)

        assert result["Success"] is False
        assert result["Error"]["Code"] == "AWSError"
        assert "Access denied" in result["Error"]["Message"]
