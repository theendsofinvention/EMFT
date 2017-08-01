Building EMFT
=============

.. contents::

Installing EMFT as developer
----------------------------

To install EMFT, you'll first need to clone the repository::

    git clone https://github.com/132nd-etcher/EMFT.git

Then, make *SURE* your virtualenv is active, and install with::

    pip install -e .

Compiling EMFT
--------------

.. important:: EMFT only compiles on a Windows platform, and against Python 3.6 or newer.

EMFT is meant to be compiled as a single Win32 portable executable file.

To facilitate the building process, it is self-contained in the ``emft/build.py`` python script.

The script is installed as an executable when you install EMFT and available as ``emft-build``, which I'll explain
below.

Helper applications
+++++++++++++++++++

.. tip:: You will need to manually install these two applications if you want to build EMFT locally

gitversion.exe
**************

GitVersion is used to infer the current version from the Git repository.

``setuptools_scm`` plans on switching to using the Semver scheme in the future; when that happens,
I\'ll remove the dependency to GitVersion.

In the meanwhile, GitVersion can be obtained via Chocolatey (recommended):
https://chocolatey.org/packages/GitVersion.Portable

Or directly from: https://github.com/GitTools/GitVersion/releases

verpatch
********

Verpatch is used to embed resources like the version after the compilation.

I\'m waiting on ``pyinstaller`` to fix their own resources patcher so I can remove the dependency to
this external tool...

In the meanwhile, Verpatch can be obtained at: https://ddverpatch.codeplex.com/releases

The emft-build tool
-------------------

.. click:: emft.build:cli
    :prog: emft-build
    :show-nested:

build.py API
++++++++++++

.. automodule:: emft.build
    :members:
    :noindex:
