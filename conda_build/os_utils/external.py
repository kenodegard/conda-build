# Copyright (C) 2014 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import stat
from glob import glob
from os.path import expanduser, isfile, join

from conda.base.context import context

from ..utils import on_win


def find_executable(executable, prefix=None, all_matches=False):
    # dir_paths is referenced as a module-level variable
    #  in other code
    global dir_paths
    result = None
    if on_win:
        dir_paths = [
            join(context.root_prefix, "Scripts"),
            join(context.root_prefix, "Library\\mingw-w64\\bin"),
            join(context.root_prefix, "Library\\usr\\bin"),
            join(context.root_prefix, "Library\\bin"),
        ]
        if prefix:
            dir_paths[0:0] = [
                join(prefix, "Scripts"),
                join(prefix, "Library\\mingw-w64\\bin"),
                join(prefix, "Library\\usr\\bin"),
                join(prefix, "Library\\bin"),
            ]
    else:
        dir_paths = [
            join(context.root_prefix, "bin"),
        ]
        if prefix:
            dir_paths.insert(0, join(prefix, "bin"))

    dir_paths.extend(os.environ["PATH"].split(os.pathsep))
    if on_win:
        exts = (".exe", ".bat", "")
    else:
        exts = ("",)

    all_matches_found = []
    for dir_path in dir_paths:
        for ext in exts:
            path = expanduser(join(dir_path, executable + ext))
            if isfile(path):
                st = os.stat(path)
                if on_win or st.st_mode & stat.S_IEXEC:
                    if all_matches:
                        all_matches_found.append(path)
                    else:
                        result = path
                        break
        if not result and any([f in executable for f in ("*", "?", ".")]):
            matches = glob(os.path.join(dir_path, executable), recursive=True)
            if matches:
                if all_matches:
                    all_matches_found.extend(matches)
                else:
                    result = matches[0]
                    break
        if result:
            break
    return result or all_matches_found


def find_preferably_prefixed_executable(
    executable, build_prefix=None, all_matches=False
):
    found = find_executable("*" + executable, build_prefix, all_matches)
    if not found:
        # It is possible to force non-prefixed exes by passing os.sep as the
        # first character in executable. basename makes this work.
        found = find_executable(os.path.basename(executable), build_prefix)
    return found
