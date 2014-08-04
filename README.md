#TripleEdit

This is a Django application for editing RDF data.  It's a proof-of-concept and has only been tested with one triple store.  In principle, it should work with any triple store that you can write to from Python code.

It makes use of two JavaScript widgets - [ckeditor](http://ckeditor.com/) and [Select2](http://ivaynberg.github.io/select2/) - to make an easy to use interface for would-be editors.  The default interface is built with [HTML5 boilerplate](http://www.initializr.com/try) and is repsonsive.

##Use cases

 * a "VIVO manager"-type application that allows researchers to manager and update their research profiles.
 * a mobile or table application that allows for straightforward editing of a subset of triple store data by end users.
 * data curating or cleaning tool.  SPARQL queries could pull problematic data from your triple-store and the built in widgets (or new widgets) could be used by staff to clean or augment the data.

##Install

 * clone the repository
 * create a Python virtualenv and activate it
 * run `pip install -r requirements.txt` to install the required modules
 * copy the `.sample-env` file to `.env` and adjust the settings to match your local environment
    * You will need access to a SPARQL endpoint for read queries
    * You will need access to a VIVO instance for writing data changes
 * run `python manage.py runserver` to start up the Django development serve
 * visit `http://localhost:8000` in your browser.  There should be a listing of people and organizations if your connection to a SPARQL endpoint is configured properly and there is people and organization data in the triple store you are querying.

##Dependencies

 * A SPARQL endpoint to issue queries against.  VIVO implementors should see [setting up a SPARQL endpoint](https://wiki.duraspace.org/display/VIVO/Setting+up+a+VIVO+SPARQL+Endpoint).
 * A "backend" to write the updated data to.  See below.  This application was developed with [VIVO](http://vivoweb.org) in mind so there is a bundled VIVO backend that works with version of VIVO > 1.6.

##Backends

 For now there is a notion of a backend where edited data will be written to.  There is a bundled `VivoBackend` that's able to write data to a VIVO instance.  If you wanted to write your own backend class it would need an `add_remove` method that accepts a RDFLib graph of additions and subtractions.  That's it.  Again, this is for demonstration purposes so it will require some tinkering and original code to connect to a different backend.

