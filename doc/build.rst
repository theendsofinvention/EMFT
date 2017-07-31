Documentation for build.py
==========================



Building EMFT
-------------

EMFT is meant to be compiled as a single Win32 portable executable file.

.. attention:: You will need to manually install two helper application to fully build EMFT


``gitversion.exe``

    GitVersion is used to infer the current version from the Git repository.

    setuptools_scm plans on switching to using the Semver scheme in the future; when that happens,
    I\'ll remove the dependency to GitVersion.

    In the meanwhile, GitVersion can be obtained via Chocolatey (recommended):
    https://chocolatey.org/packages/GitVersion.Portable

    Or directly from: https://github.com/GitTools/GitVersion/releases

``verpatch.exe``

    Verpatch is used to embed resources like the version after the compilation.

    I\'m waiting on PyInstaller to fix their own resources patcher so I can remove the dependency to
    this external tool...

    In the meanwhile, "verpatch" can be obtained at: https://ddverpatch.codeplex.com/releases


.. click:: emft.build:cli
    :prog: hello-world
    :show-nested:

The whole compilation processed is handled by the ``setup.py`` script.

.. code-block:: python

   python setup.py [command] [options]

Conventions:

:Command name:



    :Command: Command line to start the tool

    :Description: Description of what the tool does

    :Depends on: Other commands the tool relies on



                Those other commands will be run *before* the tool, in the order indicated

    :Options: Available options for the tool



        The available commands are:

:pylint:

    :Command: ``python setup.py pylint``
    :Description: runs pylint against the source

    :Depends on:

        #. install_check_dependencies

.. automodule:: setup
    :members:
