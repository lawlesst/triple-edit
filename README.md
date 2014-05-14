#triple-edit

A Django application for editing RDF data.

##Install

 * clone the repository
 * create a Python virtualenv and activate it
 * run `pip install -r requirements.txt` to install the required modules
 * copy the `.sample-env` file to `.env` and adjust the settings to match your local environment
    * You will need access to a SPARQL endpoint for read queries
    * You will need access to a VIVO instance for writing data changes
 * run `python manage.py runserver` to start up the Django development serve

 ##Backends
 For now there is a notion of a backend where edited data will be written.  It's defaulting to
 a VIVO 1.5 backend.  If your environment is configured properly in `.env` then you are ready to 
 begin testing the application.  To set a backend, adjust the code in views.py, begining on line 13
 to match your situation.

##Managing the application.

Documentation needed:
 * Changing display and edit sections
 * Changing SPARQL queries
 * Adding functionality to the data edits.