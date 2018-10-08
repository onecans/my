mystock
=======


http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1990-12-19&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1991-05-17&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1992-11-20&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1994-07-29&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1994-08-01&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=1999-05-18&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=2005-07-19&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=2008-10-28&final__exact=1&o=2.3
http://127.0.0.1:8000/admin/datareader/periodmincnt/?q=2014-07-21&final__exact=1&o=2.3


My Stock

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run manage.py test
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ py.test

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd mystock
    celery -A mystock.taskapp worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.



Usage:
    http://127.0.0.1:8000/datareader/k_search



Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://sentry.io/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

The following details how to deploy this application.




