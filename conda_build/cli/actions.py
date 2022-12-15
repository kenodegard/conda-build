# SPDX-FileCopyrightText: © 2012 Continuum Analytics, Inc. <http://continuum.io>
# SPDX-FileCopyrightText: © 2017 Anaconda, Inc. <https://www.anaconda.com>
# SPDX-License-Identifier: BSD-3-Clause
import argparse


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, items, option_string=None):
        setattr(namespace, self.dest, dict())

        for item in items:
            key, value = item.split('=')
            if key in getattr(namespace, self.dest):
                raise KeyError(
                        f"Key {key} cannot be overwritten. "
                        "It's likely that the key you've used "
                        "is already in use by conda-build."
                        )
            getattr(namespace, self.dest)[key] = value
