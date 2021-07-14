import argparse
import glob
import logging
# import platform
import subprocess
import unittest
import yaml
from string import Template


# The unit test "container" class
class AtomicUnitTests(unittest.TestCase):
    longMessage = True


# Funtion to use executor to fire test
def atomic_unit_test(command, executor=None, timeout=None):
    # The unit test function
    def test(self):
        logging.debug(f"Attempting Command:\n{command}\n")
        description = f"\n\nCommand:\n{command}"
        result = False
        # Wrap in Try/Except for failure states
        try:
            # Per-Executor Type Assertions
            if executor['name'] in ('sh', 'command_prompt'):
                result = subprocess.run(
                    command,
                    shell=True, capture_output=True,
                    timeout=timeout
                )
            elif executor['name'] == 'powershell':
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    capture_output=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(command, capture_output=True)

            logging.debug(
                "Command Result:\n%s\n" % result.stdout.decode("utf-8")
            )
            logging.debug(f"Command Process:\n{result}\n")

            # Check for other kinds of failure
            if result.returncode != 0:
                description += "\n\nError [%s]:\n%s" % (
                    result.returncode,
                    result.stderr.decode("utf-8")
                )
                result = False

        # If nothing worked...
        except Exception as e:
            description += "\n\nError:\n%s" % e
            result = False

        # Account for "elevated_required" flags in failure
        if result is False and executor.get('elevation_required'):
            description += "\n[ELEVATION REQUIRED]"

        # Perform the success/fail with message
        self.assertIsNot(result, False, description)

    return test
    # END def test
# END def atomic_unit_test


# Helper to open a single YAML file
def open_yaml_file(yaml_file):
    logging.debug(f"Loading YAML File: '{yaml_file}'\n")
    try:
        return yaml.load(open(yaml_file), Loader=yaml.FullLoader)
    except (
        FileNotFoundError, IsADirectoryError, OSError, UnicodeDecodeError,
        yaml.scanner.ScannerError, yaml.parser.ParserError
    ) as e:
        logging.error("Failed to load '%s'.\n%s\n" % (yaml_file, e))
        return False


# Helper Class for Input Argument Parsing
class AtomicCommandTemplate(Template):
    delimiter = "#"


# Helper Function for Input Argument Parsing
def process_command_inputs(command, input_arguments):
    return AtomicCommandTemplate(command).safe_substitute(input_arguments)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--atomics',
        help='''
            Target a directory of (local) atomics YAML files, load all.
        ''',
    )
    parser.add_argument(
        '--config',
        help='''
            Specify a (local) YAML file which associates GUID's and inputs.
        ''',
    )
    parser.add_argument(
        '--only', action='store_true',
        help='''
            Only run tests included in the loaded 'config' file.
        ''',
    )
    parser.add_argument(
        '--timeout', type=int,
        help='''
            Set the timeout in seconds for running commands (default: None).
        ''',
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='''
            See all messages, commands, etc.
        ''',
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug("Running...\n")

    # If a config file provided, use its input arguments
    pre_config_atomics = {}
    if args.config:
        current_yaml = open_yaml_file(args.config)
        if current_yaml is False:
            # Bail if config fails to load
            print(f"Failed to load '{args.config}'. Exiting.")
            exit()
        else:
            # Loop if YAML is good
            for atomic_test in current_yaml.get('atomic_tests', []):
                # If needed, add object to dict
                if pre_config_atomics.get(atomic_test['guid']) is None:
                    pre_config_atomics[atomic_test['guid']] = {}
                # Only if 'input_arguments' is configured ...
                if atomic_test.get('input_arguments'):
                    # ... assign the 'input_arguments'
                    pre_config_atomics[atomic_test['guid']][
                        'input_arguments'
                        ] = atomic_test.get('input_arguments')
            # END for atomic_test
        # END if current_yaml
    # END if args.config

    # Load in directory of YAML
    logging.debug(f"Loading Directory: '{args.atomics}'\n")
    yaml_files = glob.glob("%s/*.yaml" % args.atomics)
    # Loop the files
    for yaml_file in yaml_files:
        # Try to load them in...
        current_yaml = open_yaml_file(yaml_file)
        if current_yaml is False:
            # If YAML is no good, skip it
            logging.info(f"Skipping {yaml_file}...")
            continue

        # Walk through Atomic Tests
        for atomic_test in current_yaml.get('atomic_tests', []):
            # See if we are only running the 'config' tests
            if args.only:
                if atomic_test['auto_generated_guid'] \
                        not in pre_config_atomics:
                    logging.debug(f"Skipping Test: '{atomic_test['name']}'.\n")
                    continue

            # Process the input arugments
            processed_inputs = {}
            for in_arg in atomic_test.get('input_arguments', []):
                # First, see if one has been pre-configured
                pre_config_input = pre_config_atomics.get(
                    atomic_test['auto_generated_guid'], {}
                ).get('input_arguments', {}).get(in_arg, {}).get('value')
                # If it is pre-defined, use it...
                if pre_config_input:
                    processed_inputs[in_arg] = pre_config_input
                else:
                    # ... otherwise, use default.
                    processed_inputs[in_arg] = \
                        atomic_test['input_arguments'][in_arg].get('default')
            # END for in_arg

            # Add the inputs to the command
            command = process_command_inputs(
                atomic_test.get('executor').get('command'),
                processed_inputs
            )

            # Fire each line of the test!
            i = 0
            for current_line in command.splitlines():
                # Define the atomic test to execute
                test_func = atomic_unit_test(
                    current_line,
                    atomic_test.get('executor'),
                    args.timeout
                )
                # Use a unique name
                test_name = "test_%s | %s [%s] (%s)" % (
                    current_yaml.get('attack_technique'),
                    atomic_test.get('name'), i,
                    atomic_test.get('auto_generated_guid')
                )
                # Create the test
                setattr(AtomicUnitTests, test_name, test_func)
                # Add to counter
                i += 1
            # END for current_line
        # END for atomic_test
    # END for yaml_file

    unittest.main(argv=[''])
    logging.debug("Done!")
