# Copyright (C) 2014 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
import os.path
import sys

# expose source code for import
sys.path.insert(0, os.path.abspath("../.."))

import conda_build  # noqa: E402

# -- Project information -----------------------------------------------------

project = "conda-build"
copyright = "2018, Anaconda, Inc."
author = "Anaconda, Inc."
version = release = conda_build.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "autoapi.extension",
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx_reredirects",
    "sphinx_sitemap",
]


# Leave double dashes as they are in the docs. Don't replace -- with -
smartquotes = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_style = "css/custom.css"

# The name of an image file (relative to this directory) to use as a favicon of
# the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "img/conda-logo.png"

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
html_extra_path = [
    # Serving the robots.txt since we want to point to the sitemap.xml file
    "robots.txt",
]

# Setting the prod URL of the site here as the base URL.
html_baseurl = f"https://docs.conda.io/projects/{project}/"

html_theme_options = {
    # The maximum depth of the table of contents tree. Set this to -1 to allow
    # unlimited depth.
    "navigation_depth": -1,
}


# -- For sphinx.ext.intersphinx --------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
}


# -- For sphinx_sitemap ----------------------------------------------------

sitemap_locales = [None]
sitemap_url_scheme = "{lang}stable/{link}"


# -- For myst_parser -------------------------------------------------------

myst_heading_anchors = 3
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]


# -- For sphinx.ext.todo ---------------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# -- For autoapi.extension -------------------------------------------------

autoapi_dirs = ["../../conda_build"]
autoapi_root = "dev-guide/api"
# Manually inserted into TOC in dev-guide/api.rst for proper integration into
# folder-view
autoapi_add_toctree_entry = False
autoapi_template_dir = "_templates/autoapi"


# -- For sphinx_reredirects ------------------------------------------------

redirects = {}
