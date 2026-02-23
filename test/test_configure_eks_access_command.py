"""Tests for configure_eks_access command."""

import unittest
from unittest.mock import Mock

from telco_cli.commands.configure_eks_access import ConfigureEksAccessCommand


class TestConfigureEksAccessCommand(unittest.TestCase):
    """Test cases for ConfigureEksAccessCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ConfigureEksAccessCommand()

    def test_name_property(self):
        """Test command name property."""
        self.assertEqual(self.command.name, "configure-eks-access")

    def test_description_property(self):
        """Test command description property."""
        self.assertIsInstance(self.command.description, str)
        self.assertGreater(len(self.command.description), 0)

    def test_register_arguments(self):
        """Test argument registration."""
        parser = Mock()
        self.command.register(parser)
        self.assertTrue(parser.add_argument.called)


if __name__ == "__main__":
    unittest.main()
