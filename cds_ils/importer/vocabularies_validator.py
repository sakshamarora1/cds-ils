# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
#
# cds-migrator-kit is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Vocabularies validator."""

import json
import os
import pathlib

from invenio_app_ils.proxies import current_app_ils

from cds_ils.migrator.errors import VocabularyError

CURRENT_DIR = pathlib.Path(__file__).parent.absolute()

VOCABULARIES_TYPE_FILENAME = {
    "alternative_identifier_scheme": "alternative_identifier_schemes.json",
    "alternative_title_type": "alternative_title_types.json",
    "affiliation_identifier_scheme": "author_affiliation_identifier_schemes.json",  # noqa
    "author_identifier_scheme": "author_identifier_schemes.json",
    "author_role": "author_roles.json",
    "author_type": "author_types.json",
    "identifier_scheme": "identifier_schemes.json",
    "doc_identifiers_materials": "document_identifiers_materials.json",
    "document_accelerators": "document_accelerators.json",
    "document_experiments": "document_experiments.json",
    "document_standard_reviews": "document_standard_reviews.json",
    "document_institutions": "document_institutions.json",
    "doc_subjects": "document_subjects.json",
    "conference_identifier_scheme": "conference_identifier_schemes",
    "tag": "tags.json",
    "series_url_access_restriction": "series_url_access_restrictions.json",
    "series_identifier_scheme": "series_identifier_schemes.json",
    "acq_medium": "acq_order_line_mediums.json",
    "acq_order_line_payment_mode": "acq_order_line_payment_modes.json",
    "acq_order_line_purchase_type": "acq_order_line_purchase_types.json",
    "acq_recipient": "acq_order_line_recipients.json",
    "acq_payment_mode": "acq_payment_modes.json",
    "currencies": "currencies.json",
    "doc_req_medium": "docreq_mediums.json",
    "doc_req_payment_method": "docreq_payment_methods.json",
    "doc_req_type": "docreq_request_types.json",
    "ill_payment_mode": "ill_payment_modes.json",
    "ill_item_type": "ill_item_types.json",
    "item_medium": "item_mediums.json",
    "provider_type": "provider_types.json",
}


def json_fetcher(vocab_type, _):
    """Fetch all values for the given type from the vocab JSON file."""
    filename = VOCABULARIES_TYPE_FILENAME[vocab_type]
    filepath = os.path.join(
        os.path.realpath("."), "cds_ils", "vocabularies", "data", filename
    )
    with open(filepath) as fp:
        data = json.load(fp)
        return [d["key"] for d in data]


def es_fetcher(vocab_type, key):
    """Return the key if it exists in the vocabulary in ES."""
    vocabulary_search = current_app_ils.vocabulary_search_cls()
    search = vocabulary_search.search_by_type_and_key(type=vocab_type, key=key)
    count = search.count()
    if count == 1:
        return key


class Validator(object):
    """Vocabulary values validator."""

    CACHE = dict()

    def _fetch(self, vocab_type, key, definition):
        """Fetch vocabulary key from its source."""
        source = definition["source"]
        if source == "json":
            values = json_fetcher(vocab_type, key)
            return set(values) if values else set()
        elif source == "elasticsearch":
            value = es_fetcher(vocab_type, key)
            return set([value]) if value is not None else set()
        else:
            raise VocabularyError(
                "Definition {0} is wrong, unknown source {1}".format(
                    definition, source
                )
            )

    def _vocab_has_key(self, vocab_type, key, definition):
        """Return True if key is in cache or in source, updating cache."""
        self.CACHE.setdefault(vocab_type, set())
        cache_has_key = key in self.CACHE[vocab_type]
        if not cache_has_key:
            keys = self._fetch(vocab_type, key, definition)
            cache_has_key = key in keys
            if cache_has_key:
                # add all keys to the CACHE set
                self.CACHE[vocab_type] |= keys
                return True
            else:
                return False
        return True

    def _validate_vocab_field(self, definition, key):
        """Raise if vocab key does not exist."""
        vocab_type = definition["type"]
        vocab_has_key = self._vocab_has_key(vocab_type, key, definition)
        if not vocab_has_key:
            raise VocabularyError(
                "Value {0} not found in vocabulary {1}".format(key, vocab_type)
            )

    def validate(self, definitions, record):
        """Traverse each vocab field and validate the existence of values."""
        for field, value in record.items():
            has_definition = field in definitions
            if not has_definition:
                # field should not be validated
                continue

            definition = definitions[field]
            # field should be validated
            if isinstance(value, dict):
                self.validate(definition, value)
            elif isinstance(value, list):
                # list can contain a list of values or objs
                for el in value:
                    if isinstance(el, dict):
                        self.validate(definition, el)
                    else:
                        self._validate_vocab_field(definition, el)
            else:
                self._validate_vocab_field(definition, value)

    def reset(self):
        """Invalidate cache."""
        self.CACHE = dict()


validator = Validator()
