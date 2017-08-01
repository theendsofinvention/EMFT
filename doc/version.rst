Versionning scheme
------------------

EMFT follows the SemVer_ specification.

GitVersion_ is used to infer the current version from the Git repository.

============== ===============================
 Branch         Tag
============== ===============================
 master
 support
 hotfix         patch
 release        exp
 develop        beta
 feature        alpha.[FEATURE_NAME]
 pull request   alpha.PullRequest.[PR_NUMBER]
============== ===============================

(``master`` and ``support`` do not have a pre-release tag)

(feature, pull request) < develop < release < hotfix < (master, support)

.. figure:: _images/versionning.png
    :target: _images/versionning.png
    :scale: 50 %
    :alt: EMFT versionning scheme

    EMFT versionning scheme (click the picture for larger scale)


.. _SemVer: http://semver.org/
.. _GitVersion: https://github.com/GitTools/GitVersion
