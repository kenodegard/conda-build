# Copyright (C) 2014 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import conda_build.utils
from conda_build import api, post
from conda_build.exceptions import CondaBuildUserError
from conda_build.utils import (
    get_site_packages,
    on_linux,
    on_mac,
    on_win,
    package_has_file,
)

from .utils import add_mangling, metadata_dir, subpackage_path

if TYPE_CHECKING:
    from conda.testing import PathFactoryFixture
    from pytest import CaptureFixture


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason="Python 3.10+, py_compile terminates once it finds an invalid file",
)
def test_compile_missing_pyc(testing_workdir):
    good_files = ["f1.py", "f3.py"]
    bad_file = "f2_bad.py"
    tmp = os.path.join(testing_workdir, "tmp")
    shutil.copytree(
        os.path.join(
            os.path.dirname(__file__), "test-recipes", "metadata", "_compile-test"
        ),
        tmp,
    )
    post.compile_missing_pyc(os.listdir(tmp), cwd=tmp, python_exe=sys.executable)
    for f in good_files:
        assert os.path.isfile(os.path.join(tmp, add_mangling(f)))
    assert not os.path.isfile(os.path.join(tmp, add_mangling(bad_file)))


def test_hardlinks_to_copies():
    with open("test1", "w") as f:
        f.write("\n")

    os.link("test1", "test2")
    assert os.lstat("test1").st_nlink == 2
    assert os.lstat("test2").st_nlink == 2

    post.make_hardlink_copy("test1", os.getcwd())
    post.make_hardlink_copy("test2", os.getcwd())

    assert os.lstat("test1").st_nlink == 1
    assert os.lstat("test2").st_nlink == 1


def test_postbuild_files_raise(testing_metadata):
    fn = "buildstr", "buildnum", "version"
    for f in fn:
        with open(
            os.path.join(testing_metadata.config.work_dir, f"__conda_{f}__.txt"), "w"
        ) as fh:
            fh.write("123")
        with pytest.raises(ValueError, match=f):
            post.get_build_metadata(testing_metadata)


@pytest.mark.skipif(on_win, reason="fix_shebang is not executed on win32")
def test_fix_shebang():
    fname = "test1"
    with open(fname, "w") as f:
        f.write("\n")
    os.chmod(fname, 0o000)
    post.fix_shebang(fname, ".", "/test/python")
    assert os.stat(fname).st_mode == 33277  # file with permissions 0o775


def test_postlink_script_in_output_explicit(testing_config):
    recipe = os.path.join(metadata_dir, "_post_link_in_output")
    pkg = api.build(recipe, config=testing_config, notest=True)[0]
    assert package_has_file(pkg, "bin/.out1-post-link.sh") or package_has_file(
        pkg, "Scripts/.out1-post-link.bat"
    )


def test_postlink_script_in_output_implicit(testing_config):
    recipe = os.path.join(metadata_dir, "_post_link_in_output_implicit")
    pkg = api.build(recipe, config=testing_config, notest=True)[0]
    assert package_has_file(pkg, "bin/.out1-post-link.sh") or package_has_file(
        pkg, "Scripts/.out1-post-link.bat"
    )


def test_pypi_installer_metadata(testing_config):
    recipe = os.path.join(metadata_dir, "_pypi_installer_metadata")
    pkg = api.build(recipe, config=testing_config, notest=True)[0]
    expected_installer = "{}/imagesize-1.1.0.dist-info/INSTALLER".format(
        get_site_packages("", "3.9")
    )
    assert "conda" == (package_has_file(pkg, expected_installer, refresh_mode="forced"))


def test_menuinst_validation_ok(testing_config, caplog, tmp_path):
    "1st check - validation passes with recipe as is"
    recipe = Path(metadata_dir, "_menu_json_validation")
    recipe_tmp = tmp_path / "_menu_json_validation"
    shutil.copytree(recipe, recipe_tmp)

    with caplog.at_level(logging.INFO):
        pkg = api.build(str(recipe_tmp), config=testing_config, notest=True)[0]

    captured_text = caplog.text
    assert "Found 'Menu/*.json' files but couldn't validate:" not in captured_text
    assert "not a valid menuinst JSON file" not in captured_text
    assert "is a valid menuinst JSON document" in captured_text
    assert package_has_file(pkg, "Menu/menu_json_validation.json")


def test_menuinst_validation_fails_bad_schema(testing_config, caplog, tmp_path):
    "2nd check - valid JSON but invalid content fails validation"
    recipe = Path(metadata_dir, "_menu_json_validation")
    recipe_tmp = tmp_path / "_menu_json_validation"
    shutil.copytree(recipe, recipe_tmp)
    menu_json = recipe_tmp / "menu.json"
    menu_json_contents = menu_json.read_text()

    bad_data = json.loads(menu_json_contents)
    bad_data["menu_items"][0]["osx"] = ["bad", "schema"]
    menu_json.write_text(json.dumps(bad_data, indent=2))
    with caplog.at_level(logging.WARNING):
        api.build(str(recipe_tmp), config=testing_config, notest=True)

    captured_text = caplog.text
    assert "Found 'Menu/*.json' files but couldn't validate:" not in captured_text
    assert "not a valid menuinst JSON document" in captured_text
    assert "ValidationError" in captured_text


def test_menuinst_validation_fails_bad_json(testing_config, monkeypatch, tmp_path):
    "3rd check - non-parsable JSON fails validation"
    recipe = Path(metadata_dir, "_menu_json_validation")
    recipe_tmp = tmp_path / "_menu_json_validation"
    shutil.copytree(recipe, recipe_tmp)
    menu_json = recipe_tmp / "menu.json"
    menu_json_contents = menu_json.read_text()
    menu_json.write_text(menu_json_contents + "Make this an invalid JSON")

    # suspect caplog fixture may fail; use monkeypatch instead.
    records = []

    class MonkeyLogger:
        def __getattr__(self, name):
            return self.warning

        def warning(self, *args, **kwargs):
            records.append((*args, kwargs))

    monkeylogger = MonkeyLogger()

    def get_monkey_logger(*args, **kwargs):
        return monkeylogger

    # For some reason it uses get_logger in the individual functions, instead of
    # a module-level global that we could easily patch.
    monkeypatch.setattr(conda_build.utils, "get_logger", get_monkey_logger)

    api.build(str(recipe_tmp), config=testing_config, notest=True)

    # without %s substitution
    messages = [record[0] for record in records]

    assert "Found 'Menu/*.json' files but couldn't validate: %s" not in messages
    assert "'%s' is not a valid menuinst JSON document!" in messages
    assert any(
        isinstance(record[-1].get("exc_info"), json.JSONDecodeError)
        for record in records
    )


def test_file_hash(testing_config, caplog, tmp_path):
    "check that the post-link check caching takes the file path into consideration"
    recipe = Path(subpackage_path, "_test-file-hash")
    recipe_tmp = tmp_path / "test-file-hash"
    shutil.copytree(recipe, recipe_tmp)

    variants = {"python": ["3.11", "3.12"]}
    testing_config.ignore_system_config = True
    testing_config.activate = True

    with caplog.at_level(logging.INFO):
        api.build(
            str(recipe_tmp),
            config=testing_config,
            notest=True,
            variants=variants,
            activate=True,
        )


@pytest.mark.skipif(on_win, reason="rpath fixup not done on Windows.")
def test_rpath_symlink(mocker, testing_config):
    if on_linux:
        mk_relative = mocker.spy(post, "mk_relative_linux")
    elif on_mac:
        mk_relative = mocker.spy(post, "mk_relative_osx")
    api.build(
        os.path.join(metadata_dir, "_rpath_symlink"),
        config=testing_config,
        variants={"rpaths_patcher": ["patchelf", "LIEF"]},
        activate=True,
    )
    # Should only be called on the actual binary, not its symlinks. (once per variant)
    assert mk_relative.call_count == 2


def test_check_dist_info_version():
    # package not installed
    post.check_dist_info_version("name", "1.2.3", [])

    # package installed and version matches
    post.check_dist_info_version("name", "1.2.3", ["name-1.2.3.dist-info/METADATA"])

    # package installed and version does not match
    with pytest.raises(CondaBuildUserError):
        post.check_dist_info_version("name", "1.2.3", ["name-1.0.0.dist-info/METADATA"])


def test_find_lib(capsys: CaptureFixture, tmp_path: Path) -> None:
    (prefix := tmp_path / "prefix").mkdir()
    (prefix / (file1 := (name := "name"))).write_text("content")
    (prefix / (dirA := "dirA")).mkdir()
    (prefix / (file2 := f"{dirA}{os.sep}{name}")).write_text("content")
    (prefix / (dirB := "dirB")).mkdir()
    (prefix / (file3 := f"{dirB}{os.sep}{name}")).write_text("other")

    (external := tmp_path / "external").mkdir()

    rpath = Path("@rpath")
    executable_path = Path("@executable_path")

    # /prefix/missing is in prefix but isn't in file list (i.e., doesn't exist)
    with pytest.raises(CondaBuildUserError, match=r"Could not find"):
        post.find_lib(prefix / "missing", prefix, [])

    # /prefix/name is in prefix and is in file list (i.e., it exists)
    assert post.find_lib(prefix / name, prefix, [file1]) == file1

    # /external/name is not in prefix
    assert post.find_lib(external / name, prefix, []) is None

    # @rpath/name paths are assumed to already point to a valid file
    assert post.find_lib(rpath / name, prefix, []) is None
    assert post.find_lib(rpath / "extra" / name, prefix, []) is None

    # name is in the file list
    assert post.find_lib(name, prefix, [file1]) == file1
    assert post.find_lib(name, prefix, [file2]) == file2

    # @executable_path/name is in the file list
    assert post.find_lib(executable_path / name, prefix, [file1]) == file1
    assert post.find_lib(executable_path / name, prefix, [file2]) == file2

    # @executable_path/extra/name is in the file list
    # TODO: is this valid?
    assert post.find_lib(executable_path / "extra" / name, prefix, [file1]) == file1
    assert post.find_lib(executable_path / "extra" / name, prefix, [file2]) == file2

    # name matches multiples in the file list (and they're all the same file)
    capsys.readouterr()  # clear buffer
    assert post.find_lib(name, prefix, [file1, file2]) == file2
    stdout, stderr = capsys.readouterr()
    assert stdout == (
        f"Found multiple instances of {name!r}: {[file2, file1]!r}. "
        f"Choosing the first one.\n"
    )
    assert not stderr

    # name matches multiples in file list (and they're not the same file)
    with pytest.raises(CondaBuildUserError, match=r"Found multiple instances"):
        post.find_lib(name, prefix, [file1, file3])

    # missing is not in the file list
    with pytest.raises(CondaBuildUserError, match=r"Could not find"):
        post.find_lib("missing", prefix, [file1, file2])

    # name matches multiples in file list but an explicit path is given
    assert post.find_lib(name, prefix, [file1, file2, file3], file1) == file1
    assert post.find_lib(name, prefix, [file1, file2, file3], file2) == file2
    assert post.find_lib(name, prefix, [file1, file2, file3], file3) == file3

    # relative/name is not in prefix and doesn't match any of the files
    capsys.readouterr()  # clear buffer
    assert post.find_lib(link := Path("relative", name), prefix, []) is None
    stdout, stderr = capsys.readouterr()
    assert stdout == f"Don't know how to find '{link}', skipping\n"
    assert not stderr


def test_osx_ch_link_missing(path_factory: PathFactoryFixture):
    path = path_factory()
    host_prefix = path_factory()
    build_prefix = path_factory()

    with pytest.raises(
        CondaBuildUserError,
        match="Compiler runtime library in build prefix not found in host prefix",
    ):
        post.osx_ch_link(
            str(path),
            {"name": str(build_prefix / "missing")},
            str(host_prefix),
            str(build_prefix),
            [],
        )


def test_check_symlinks_error(path_factory: PathFactoryFixture):
    (prefix := path_factory()).mkdir()
    (croot := path_factory()).mkdir()

    (real := croot / "real").touch()
    (prefix / (link := "link")).symlink_to(real)
    (prefix / (link2 := "link2")).symlink_to(real)

    with pytest.raises(
        CondaBuildUserError,
        match=(
            r"Found symlinks to paths that may not exist after the build is completed:\n"
            rf"  link → {real}\n"
            rf"  link2 → {real}"
        ),
    ):
        post.check_symlinks([link, link2], str(prefix), str(croot))
