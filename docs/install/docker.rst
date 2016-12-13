######
Docker
######

Want to use Docker? More on this later. For now you may look at the ``docker``
directory at the top of the repository on GitHub, or if you're feeling plucky,
check out the contents of :doc:`../dockerfile`.

Quick start
===========

.. code-block:: bash

   $ cd docker
   $ docker run -p 8990:8990 -d --name=nsot nsot/nsot start --noinput

README
======

Here is the readme until we clean up these docs and include them for real here.

.. literalinclude:: ../../docker/README.md
   :language: md
