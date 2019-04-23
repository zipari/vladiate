from __future__ import division
import csv
from collections import defaultdict
import time

from vladiate.exceptions import ValidationException
from vladiate.validators import EmptyValidator
from vladiate import logs


class LogFormatter:
    def __init__(self):
        self.logger = logs.logger

    def log_debug_failures(self, failures):
        raise NotImplementedError

    def log_validator_failures(self, validators):
        raise NotImplementedError

    def log_missing_validators(self):
        raise NotImplementedError


class JsonLogFormatter(LogFormatter):
    def __init__(self):
        super().__init__()

    def log_validator_failures(self, validators):
        for field_name, validators_list in validators.items():
            for validator in validators_list:
                if validator.bad:
                    self.logger.error(
                        {'validator': validator.__class__.__name__,
                         'total_failures': validator.fail_count,
                         'field_name': field_name,
                         'timestamp': int(time.time()),
                         'invalid_fields': list(validator.bad)})

    def log_debug_failures(self, failures):
        pass

    def log_missing_validators(self):
        pass


class StdoutLogFormatter(LogFormatter):
    def __init__(self):
        super().__init__()

    def log_debug_failures(self, failures):
        for field_name, field_failure in failures.items():
            self.logger.debug('\nFailure on field: "{}":'.format(field_name))
            for i, (row, errors) in enumerate(field_failure.items()):
                self.logger.debug("  {}:{}".format(self.source, row))
                for error in errors:
                    self.logger.debug("    {}".format(error))

    def log_validator_failures(self, validators):
        for field_name, validators_list in validators.items():
            for validator in validators_list:
                if validator.bad:
                    self.logger.error(
                        "  {} failed {} time(s) ({:.1%}) on field: '{}'".format(
                            validator.__class__.__name__,
                            validator.fail_count,
                            validator.fail_count / self.line_count,
                            field_name,
                        )
                    )
                    try:
                        # If self.bad is iterable, it contains the fields which
                        # caused it to fail
                        invalid = list(validator.bad)
                        shown = ["'{}'".format(field) for field in invalid[:99]]
                        hidden = ["'{}'".format(field) for field in invalid[99:]]
                        self.logger.error(
                            "    Invalid fields: [{}]".format(", ".join(shown))
                        )
                        if hidden:
                            self.logger.error(
                                "    ({} more suppressed)".format(len(hidden))
                            )
                    except TypeError:
                        pass

    def log_missing_validators(self):
        self.logger.error("  Missing validators for:")
        self.log_missing(self.missing_validators)

    def log_missing_fields(self):
        self.logger.error("  Missing expected fields:")
        self.log_missing(self.missing_fields)

    def log_missing(self, missing_items):
        self.logger.error(
            "{}".format(
                "\n".join(
                    ["    '{}': [],".format(field) for field in sorted(missing_items)]
                )
            )
        )


class Vlad(object):
    def __init__(
        self,
        source,
        validators={},
        default_validator=EmptyValidator,
        delimiter=None,
        ignore_missing_validators=False,
        log_format='stdout'
    ):
        self.logger = logs.logger
        self.failures = defaultdict(lambda: defaultdict(list))
        self.missing_validators = None
        self.missing_fields = None
        self.source = source
        self.validators = validators or getattr(self, "validators", {})
        self.delimiter = delimiter or getattr(self, "delimiter", ",")
        self.line_count = 0
        self.log_format = log_format
        self.ignore_missing_validators = ignore_missing_validators

        self.validators.update(
            {
                field: [default_validator()]
                for field, value in self.validators.items()
                if not value
            }
        )

        self.log_formatter = self._instantiate_formatter()

    def _instantiate_formatter(self):
        log_formats = frozenset(('json', 'stdout'),)
        assert self.log_format in log_formats, 'unrecognized log format'
        _class_name = '{0}LogFormatter'.format(self.log_format.capitalize())
        return globals()[_class_name](source=self.source)

    def validate(self):
        self.logger.info(
            "\nValidating {}(source={})".format(self.__class__.__name__, self.source)
        )
        reader = csv.DictReader(self.source.open(), delimiter=self.delimiter)

        if not reader.fieldnames:
            self.logger.info(
                "\033[1;33m" + "Source file has no field names" + "\033[0m"
            )
            return False

        self.missing_validators = set(reader.fieldnames) - set(self.validators)
        if self.missing_validators:
            self.logger.info("\033[1;33m" + "Missing..." + "\033[0m")
            self._log_missing_validators()

            if not self.ignore_missing_validators:
                return False

        self.missing_fields = set(self.validators) - set(reader.fieldnames)
        if self.missing_fields:
            self.logger.info("\033[1;33m" + "Missing..." + "\033[0m")
            self._log_missing_fields()
            return False

        for line, row in enumerate(reader):
            self.line_count += 1
            for field_name, field in row.items():
                if field_name in self.validators:
                    for validator in self.validators[field_name]:
                        try:
                            validator.validate(field, row=row)
                        except ValidationException as e:
                            self.failures[field_name][line].append(e)
                            validator.fail_count += 1

        if self.failures:
            self.logger.info("\033[0;31m" + "Failed :(" + "\033[0m")
            self._log_debug_failures()
            self._log_validator_failures()
            return False
        else:
            self.logger.info("\033[0;32m" + "Passed! :)" + "\033[0m")
            return True
