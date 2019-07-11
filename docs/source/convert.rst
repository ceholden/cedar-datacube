.. _convert:


=========================
Pre-ARD to ARD Conversion
=========================


Tips
====

* When specifying the ARD destination directory (either in the configuration
  file or by overriding using ``cedar convert --dest DEST``), you may wish
  to use an environment variable for the root destination directory. This
  variable will be expanded before determining the destination path. Using
  environment variables is common for batch processing because it allows
  you to manipulate variables or other data without modifying the config file.
