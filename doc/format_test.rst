Format test
===========


.. warning:: Warning

.. attention:: Attention

.. caution:: caution

.. danger:: danger

.. error:: error

.. hint:: hint

.. important:: important

.. tip:: tip

.. note:: note

.. graphviz::

   digraph foo {
      "bar" -> "baz";
   }


    digraph versionning {
        subgraph cluster0 {
            node [style=filled,color=white];
            style=filled;
            color=lightgrey;
            m0 -> m1 -> m2 -> m3;
            label = "branch: master";
        };
        subgraph cluster1 {
            rc0 -> rc1 -> rc2 rc3;
            label = "branch: release/*\ntag: exp";
        };
        subgraph cluster3 {
            b0 -> b1 -> b2 -> b3 -> b4 -> b5 -> b6 -> b7;
            label = "branch: develop/*\ntag: beta";
        };
        m0 -> b0
        b3 -> rc0
        rc2 -> b4
        rc2 -> m1
        m0 [label="0.1.0"];
        m1 [label="0.2.0"];
        m2 [label="0.3.0"];
        m3 [label="0.4.0"];
        rc0 [label="0.2.0-exp.0"];
        rc1 [label="0.2.0-exp.1"];
        rc2 [label="0.2.0-exp.2"];
        rc3 [label="0.3.0-exp.0"];
        b0 [label="0.2.1-beta.0"];
        b1 [label="0.2.1-beta.1"];
        b2 [label="0.2.1-beta.2"];
        b3 [label="0.2.1-beta.3"];
        b4 [label="0.3.1-beta.0"];
        b5 [label="0.3.1-beta.1"];
        b6 [label="0.3.1-beta.2"];
        b7 [label="0.4.1-beta.0"];
    }

.. inheritance-diagram:: emft.utils.updater.Updater
