Changelog
---------

0.11.1 (2022-03-29)
*******************

Bug fixes:

* Fix Flask 2.x support (:issue:`229`). Thanks :user:`KyleJamesWalker` for the PR.


0.11.0 (2020-10-25)
*******************

Features:

* Support apispec>=4.0.0 (:issue:`202`). Thanks :user:`kam193`.
  *Backwards-incompatible*: apispec<4.0.0 is no longer supported.

Other changes:

* *Backwards-incompatible*: Drop Python 3.5 compatibility. Only Python>=3.6 is supported.

0.10.1 (2020-10-25)
*******************

Bug fixes:

* Pin to apispec<4.0.0 (:issue:`202`). Thanks :user:`catalanojuan`.

This is the last release to support apispec<4.

0.10.0 (2020-08-27)
*******************

Features:

* Support webargs>=6 (:issue:`178`). Thanks :user:`mdantonio` for the PR.

Other changes:

* *Backwards-incompatible*: Drop Python 2 compatibility. Only Python>=3.5 is supported.
* *Backwards-incompatible*: Drop marshmallow 2 compatibility. Only marshmallow>=3.0 is supported.

0.9.0 (2020-05-27)
******************

Features:

* Add option to exclude OPTIONS requests (:issue:`111`).
  Thanks :user:`Brcrwilliams` for the PR.

0.8.8 (2020-03-29)
******************

Bug fixes:

* Fix behavior when view returns ``(obj, status_code, headers)``
  (regression in 0.8.7) (:issue:`181`).
  Thanks :user:`decaz` for reporting and thanks :user:`c-kruse`
  for the PR.

0.8.7 (2020-03-10)
******************

Bug fixes:

* Fix serialisation problem with return codes when used with flask-restful  (:issue:`98`, :issue:`93`).
  Thanks :user:`AdamLeyshon` for the PR.

0.8.6 (2020-03-01)
******************

Bug fixes:

* Restrict webargs version to <6.0 (:issue:`176`).
  Thanks :user:`c-kruse` for reporting and thanks :user:`saydamir`
  for the PR.

0.8.5 (2020-01-05)
******************

Bug fixes:

* Fix setting ``default_in`` for compatibility with newer versions of apispec (:pr:`173`).
  Thanks :user:`AbdealiJK` for the PR.

0.8.4 (2019-12-04)
******************

Bug fixes:

* Fix passing ``default_in`` argument when generating parameters (:issue:`165`).
  Thanks :user:`d42` for reporting and thanks :user:`zzz4zzz` for the fix.

0.8.3 (2019-09-17)
******************

Bug fixes:

* Fix compatibility with apispec>=3.0.0 (:issue:`163`).
  Thanks :user:`decaz`.

0.8.2 (2019-09-16)
******************

Bug fixes:

* Handle multiple locations when using use_kwargs multiple times on the same view (:issue:`78`).
  Thanks :user:`norbert-sebok` for the PR and thanks :user:`shrsubra` for updating it.

0.8.1 (2019-06-22)
******************

Bug fixes:

* Fix support for ``@post_load`` methods that return a non-dictionary object
  (:issue:`103`). Thanks :user:`erezatiya` for reporting and thanks :user:`elatomo`
  for the PR.
* Restrict marshmallow version based on Python version (:pr:`150`).

0.8.0 (2019-02-13)
******************

Features:

* Supports apispec>=1.0.0 (:issue:`130`). Older apispec versions are no longer supported.
  Thanks :user:`DStape` for the PR.
* Upgrade swagger-ui to version 3.20.7.

0.7.0 (2018-07-01)
++++++++++++++++++

Features:

* Supports apispec>=0.39.0 (:issue:`105`). Older apispec versions are no longer supported.
* Upgrade swagger-ui to version 3.17.2 (:issue:`76`). Thanks :user:`paxnovem`.

0.6.1 (2018-06-25)
++++++++++++++++++

Bug fixes:

* Fix resolution of path parameters (:issue:`92`). Thanks
  :user:`DStape` for the fix.

0.6.0 (2018-03-11)
++++++++++++++++++

Features:

* Support marshmallow 3 beta. Thanks :user:`tonycpsu` for the PR.

0.5.0 (2018-03-04)
++++++++++++++++++

Features:

* Allow a schema factory to be passed to `use_args` and `use_kwargs`
  (:issue:`79`). Thanks :user:`decaz` for the PR.

0.4.2 (2017-10-23)
++++++++++++++++++

Bug fixes:

* Fix wrapping of data parsed by schema with ``many=True``
  (:issue:`64`). Thanks :user:`decaz` for the catch and patch.

0.4.1 (2017-10-08)
++++++++++++++++++

Bug fixes:

* Include static assets for swagger-ui in distribution (:issue:`28`,
  :issue:`57`). Thanks :user:`ArthurPBressan` for reporting.

0.4.0 (2017-06-18)
++++++++++++++++++

Features:

* Add `resource_class_args` and `resource_class_kwargs` to `FlaskApiSpec.register` for passing constructor arguments to `MethodResource` classes. Thanks :user:`elatomo.`
* Add `FlaskApiSpec.init_app` method to support app factories (:issue:`21`). Thanks :user:`lafrech` for the suggestion and thanks :user:`dases` for the PR.
* Defer registering views until `init_app` is called. Thanks :user:`kageurufu` for the PR.
* Add support for documenting headers and query params (:issue:`32).` Thanks :user:`rodjjo.`
* Upon calling ``FlaskApiSpec(app)``, register rules which have already been registered on ``app`` (:issue:`48`). Thanks :user:`henryfjordan` for the fix.

Bug fixes:

* Return an empty list of parameters for undecorated views
  (:issue:`48`). Thanks :user:`henryfjordan` for the fix.

Other changes:

- Test against Python 3.6. Drop support for Python 3.3.
- Support apispec>=0.17.0. Thanks :user:`rth` for fixing support for 0.20.0.

0.3.2 (2015-12-06)
++++++++++++++++++

* Fix Swagger-UI favicons. Thanks :user:`benbeadle.`

0.3.1 (2015-11-12)
++++++++++++++++++

* Update Swagger-UI assets. Thanks :user:`evocateur.`

0.3.0 (2015-11-11)
++++++++++++++++++

* Bundle templates and static files with install. Thanks :user:`bmorgan21.`
* Use readthedocs for documentation.

0.2.0 (2015-11-03)
++++++++++++++++++

* Add `FlaskApiSpec` Flask extension.
* Serve Swagger and Swagger-UI automatically.
* Reorganize file structure.

0.1.3 (2015-11-01)
++++++++++++++++++

* Rename to flask-apispec.
* Update to latest version of apispec.

0.1.2
++++++++++++++++++

* Update to latest version of webargs.

0.1.1
++++++++++++++++++

* Restrict inheritance to HTTP verbs.

0.1.0
++++++++++++++++++

* First release.
