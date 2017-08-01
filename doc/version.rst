Versionning scheme
------------------

EMFT follows the SemVer_ specification.

GitVersion_ is used to infer the current version from the Git repository.

============== ===============================
 Branch         Tag
============== ===============================
 master         (master has no pre-release tag)
 hotfix         patch
 release        exp
 develop        beta
 feature        alpha.[FEATURE_NAME]
 pull request   alpha.PullRequest.[PR_NUMBER]
============== ===============================

.. graphviz::

    digraph foo {
        rankdir="LR";
        "hotfix\n(patch)" -> "master\n(stable)";
        "feature\n(alpha)" -> "develop\n(beta)" -> "release\n(exp)" -> "master\n(stable)";
        "Pull request\n(alpha)" -> "develop\n(beta)";

    }

.. figure:: _images/versionning.png
    :target: _images/versionning.png
    :width: 640px
    :alt: EMFT versionning scheme

    EMFT versionning scheme (click the picture for larger scale)


.. _SemVer: http://semver.org/
.. _GitVersion: https://github.com/GitTools/GitVersion
