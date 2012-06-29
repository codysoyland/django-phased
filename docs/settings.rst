.. _ref-settings:

========
Settings
========

There are 2 settings to control behavior of django-phased:

* ``PHASED_SECRET_DELIMITER``

  A custom delimiter to separate prerendered content from content that needs to
  be rendered with a second phase.

* ``PHASED_KEEP_CONTEXT``

  If set to True, this setting will automatically capture and pickle context in
  phased blocks so the second pass will have access to context variables. Use
  with caution.

