"""
Test the custom management commands.
"""

from unittest.mock import patch  # Allows us to replace real objects with mocks

# Exception for psycopg2 errors
from psycopg2 import OperationalError as Psycopg2OperationalError

# Allows us to call Django management commands
from django.core.management import call_command

# Exception for Django database errors
from django.db.utils import OperationalError

# Base class for creating simple tests without a database
from django.test import SimpleTestCase


# Patch 'core.management.commands.wait_for_db.Command.check' for all tests
# in this class
@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(SimpleTestCase):
    """Test custom Django management commands"""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for db when db is available"""

        # Simulate the database being available by setting the return value of 'check' to True.
        # This means that when 'check' is called within the 'wait_for_db' command, it will return True,
        # indicating that the database is available and ready for connections.
        patched_check.return_value = True

        # Call the custom 'wait_for_db' management command.
        # This command will internally call 'check' to see if the database is available.
        # Since we have patched 'check' to return True, the command should
        # proceed without any delays or retries.
        call_command("wait_for_db")

        # Assert that 'check' was called exactly once with the 'default' database configuration.
        # This verifies that the 'wait_for_db' command correctly checked the
        # database availability once.
        patched_check.assert_called_once_with(databases=["default"])

        # Detailed Analysis:
        # 1. The method begins by simulating a scenario where the database is available by setting
        #    'patched_check.return_value' to True. This means that any call to 'check' will return True,
        #    indicating that the database is ready.
        # 2. The 'call_command' function is used to execute the custom 'wait_for_db' management command.
        #    This function will invoke the command just as if it were run from the command line.
        # 3. The test then uses 'patched_check.assert_called_once_with(database=['default'])' to assert that
        #    the 'check' method was called exactly once with the 'default' database configuration.
        #    This ensures that the 'wait_for_db' command behaved as expected when the database was available
        #    immediately.

    # Patch 'time.sleep' in addition to 'check' to simulate waiting
    @patch("time.sleep")
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for db when getting operational errors"""

        # Simulate database connection errors followed by success:
        # First 2 attempts raise Psycopg2OperationalError,
        # Next 3 attempts raise Django's OperationalError,
        # Finally, it returns True to simulate a successful connection.
        patched_check.side_effect = (
            [Psycopg2OperationalError] * 2 + [OperationalError] * 3 + [True]
        )

        # Call the custom 'wait_for_db' management command.
        # This command will retry connecting to the database multiple times.
        call_command("wait_for_db")

        # Assert that 'check' was called 6 times in total:
        # - 2 times with Psycopg2OperationalError
        # - 3 times with OperationalError
        # - 1 time with a successful connection (True)
        self.assertEqual(patched_check.call_count, 6)

        # Assert the final call to 'check' was with the 'default' database
        patched_check.assert_called_with(databases=["default"])

        # Note: Even though 'patched_sleep' is not used directly in the code,
        # it is patched to prevent the actual sleep from happening during tests,
        # which speeds up the test execution significantly.

        # Explanation of why 'time.sleep' is patched:
        # - When 'time.sleep' is called in the actual code, it introduces a delay.
        # - Patching 'time.sleep' replaces the real sleep function with a mock that does nothing.
        # - This prevents the test from actually waiting, speeding up the test execution.
        # - It allows us to test the retry logic without incurring real-time delays.

    """
    Note: The order of parameters in the test method matches the order of @patch decorators.

    @patch('time.sleep')
    @patch('core.management.commands.wait_for_db.Command.check')
    def test_wait_for_db_delay(self, patched_check, patched_sleep):
        # The order of parameters corresponds to the order of the decorators
        # 'patched_check' comes from the second @patch, 'patched_sleep' from the first
    """
