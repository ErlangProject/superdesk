# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license


import logging
from flask import current_app as app
from flask import json
from eve.validation import ValidationError

logger = logging.getLogger(__name__)
notifiers = []


def add_notifier(notifier):
    if notifier not in notifiers:
        notifiers.append(notifier)


def update_notifiers(*args, **kwargs):
        for notifier in notifiers:
            notifier(*args, **kwargs)


def get_registered_errors(self):
        return {
            'IngestApiError': IngestApiError._codes,
            'IngestFtpError': IngestFtpError._codes,
            'IngestFileError': IngestFileError._codes
        }


class SuperdeskError(ValidationError):
    _codes = {}
    system_exception = None

    def __init__(self, code):
        self.code = code
        self.message = self._codes.get(code, 'Unknown error')

    def __str__(self):
        return "{} Error {} - {}".format(self.__class__.__name__, self.code, self.message)


class SuperdeskApiError(SuperdeskError):
    """Base class for superdesk API."""

    # default error status code
    status_code = 400

    def __init__(self, message=None, status_code=None, payload=None):
        """
        :param message: a human readable error description
        :param status_code: response status code
        :param payload: a dict with request issues
        """
        Exception.__init__(self)
        self.message = message

        if status_code:
            self.status_code = status_code

        if payload:
            self.payload = payload

        logger.error("HTTP Exception {} has been raised: {}".format(status_code, message))

    def to_dict(self):
        """Create dict for json response."""
        rv = {}
        rv[app.config['STATUS']] = app.config['STATUS_ERR']
        rv['_message'] = self.message or ''
        if hasattr(self, 'payload'):
            rv[app.config['ISSUES']] = self.payload
        return rv

    def __str__(self):
        return repr(self.status_code)

    @classmethod
    def badRequestError(cls, message=None, payload=None):
        return SuperdeskApiError(status_code=400, message=message, payload=payload)

    @classmethod
    def unauthorizedError(cls, message=None, payload={'auth': 1}):
        return SuperdeskApiError(status_code=401, message=message, payload=payload)

    @classmethod
    def forbiddenError(cls, message=None, payload=None):
        return SuperdeskApiError(status_code=403, message=message, payload=payload)

    @classmethod
    def notFoundError(cls, message=None, payload=None):
        return SuperdeskApiError(status_code=404, message=message, payload=payload)

    @classmethod
    def preconditionFailedError(cls, message=None, payload=None):
        return SuperdeskApiError(status_code=412, message=message, payload=payload)

    @classmethod
    def internalError(cls, message=None, payload=None):
        return SuperdeskApiError(status_code=500, message=message, payload=payload)


class CredentialsAuthError(SuperdeskApiError):
    """Credentials Not Match Auth Exception"""

    def __init__(self, credentials, error=None):
        super().__init__(status_code=401, payload={'credentials': 1})
        logger.warning("Login failure: %s" % json.dumps(credentials))
        if error:
            logger.error("Exception occurred: {}".format(error))


class UserInactiveError(SuperdeskApiError):
    """User is inactive, access restricted"""
    status_code = 403
    payload = {'is_active': False}
    message = 'Account suspended, access restricted.'


class IdentifierGenerationError(SuperdeskApiError):
    """Exception raised if failed to generate unique_id."""

    status_code = 500
    payload = {'unique_id': 1}
    message = "Failed to generate unique_id"


class InvalidFileType(SuperdeskError):
    """Exception raised when receiving a file type that is not supported."""

    def __init__(self, type=None):
        super().__init__('Invalid file type %s' % type, payload={})


class PrivilegeNameError(Exception):
    pass


class InvalidStateTransitionError(SuperdeskApiError):
    """Exception raised if workflow transition is invalid."""

    def __init__(self, message='Workflow transition is invalid.', status_code=412):
        super().__init__(message, status_code)


class SuperdeskIngestError(SuperdeskError):
    def __init__(self, code, exception, provider=None):
        super().__init__(code)
        self.system_exception = exception
        self.provider_name = provider.get('name', 'Unknown provider') if provider else 'Unknown provider'

        if provider.get('notifications', {}).get('on_error', True):
            update_notifiers('error',
                             'Error [%s] on ingest provider {{name}}: %s' % (code, exception),
                             name=self.provider_name)

        if provider:
            logger.error("{}: {} on channel {}".format(self, exception, self.provider_name))
        else:
            logger.error("{}: {}".format(self, exception))


class ProviderError(SuperdeskIngestError):
    _codes = {
        2001: 'Provider could not be saved',
        2002: 'Expired content could not be removed',
        2003: 'Rule could not be applied',
        2004: 'Ingest error',
        2005: 'Anpa category error',
        2006: 'Expired content could not be filtered'
    }

    @classmethod
    def providerAddError(cls, exception, provider):
        return ProviderError(2001, exception, provider)

    @classmethod
    def expiredContentError(cls, exception, provider):
        return ProviderError(2002, exception, provider)

    @classmethod
    def ruleError(cls, exception, provider):
        return ProviderError(2003, exception, provider)

    @classmethod
    def ingestError(cls, exception, provider):
        return ProviderError(2004, exception, provider)

    @classmethod
    def anpaError(cls, exception, provider):
        return ProviderError(2005, exception, provider)

    @classmethod
    def providerFilterExpiredContentError(cls, exception, provider):
        return ProviderError(2006, exception, provider)


class ParserError(SuperdeskIngestError):
    _codes = {
        1001: 'Message could not be parsed',
        1002: 'Ingest file could not be parsed',
        1003: 'ANPA file could not be parsed',
        1004: 'NewsML1 input could not be processed',
        1005: 'NewsML2 input could not be processed',
        1006: 'NITF input could not be processed',
        1007: 'WENN input could not be processed'
    }

    @classmethod
    def parseMessageError(cls, exception, provider):
        return ParserError(1001, exception, provider)

    @classmethod
    def parseFileError(cls, source, filename, exception, provider):
        logger.exception("Source Type: {} - File: {} could not be processed".format(source, filename))
        return ParserError(1002, exception, provider)

    @classmethod
    def anpaParseFileError(cls, filename, exception):
        logger.exception("File: {} could not be processed".format(filename))
        return ParserError(1003, exception)

    @classmethod
    def newsmlOneParserError(cls, exception, provider):
        return ParserError(1004, exception, provider)

    @classmethod
    def newsmlTwoParserError(cls, exception, provider):
        return ParserError(1005, exception, provider)

    @classmethod
    def nitfParserError(cls, exception, provider):
        return ParserError(1006, exception, provider)

    @classmethod
    def wennParserError(cls, exception, provider):
        return ParserError(1007, exception, provider)


class IngestFileError(SuperdeskIngestError):
    _codes = {
        3001: 'Destination folder could not be created',
        3002: 'Ingest file could not be copied'
    }

    @classmethod
    def folderCreateError(cls, exception, provider):
        return IngestFileError(3001, exception, provider)

    @classmethod
    def fileMoveError(cls, exception, provider):
        return IngestFileError(3002, exception, provider)


class IngestApiError(SuperdeskIngestError):
    _codes = {
        4000: "Unknown API ingest error",
        4001: "API ingest connection has timed out.",
        4002: "API ingest has too many redirects",
        4003: "API ingest has request error",
        4004: "API ingest Unicode Encode Error",
        4005: 'API ingest xml parse error',
        4006: 'API service not found(404) error'
    }

    @classmethod
    def apiTimeoutError(cls, exception, provider):
        return IngestApiError(4001, exception, provider)

    @classmethod
    def apiRedirectError(cls, exception, provider):
        return IngestApiError(4002, exception, provider)

    @classmethod
    def apiRequestError(cls, exception, provider):
        return IngestApiError(4003, exception, provider)

    @classmethod
    def apiUnicodeError(cls, exception, provider):
        return IngestApiError(4004, exception, provider)

    @classmethod
    def apiParseError(cls, exception, provider):
        return IngestApiError(4005, exception, provider)

    @classmethod
    def apiNotFoundError(cls, exception, provider):
        return IngestApiError(4006, exception, provider)


class IngestFtpError(SuperdeskIngestError):
    _codes = {
        5000: "FTP ingest error",
        5001: "FTP parser could not be found"
    }

    @classmethod
    def ftpError(cls, exception, provider):
        return IngestFtpError(5000, exception, provider)

    @classmethod
    def ftpUnknownParserError(cls, exception, provider, filename):
        if provider:
            logger.exception("Provider: {} - File: {} unknown file format. "
                             "Parser couldn't be found.".format(provider.get('name', 'Unknown provider'), filename))
        return IngestFtpError(5001, exception, provider)
