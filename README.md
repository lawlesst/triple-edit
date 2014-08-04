#triple-edit

This is a Django application for editing RDF data.  It's a proof-of-concept.  It was designed with the [VIVO](http://vivoweb.org) research networking system in mind, but in principle, it should work with any triple store that you can write to from Python code.

>This application was created for the [2014 VIVO Conference Apps and Tools workshop](https://www.etouches.com/ehome/80403/189150/).  There are currently no plans to maintain or support it.

##Functionality
 * [ckeditor](http://ckeditor.com/) for editing data properties containing text

 * [Select2](http://ivaynberg.github.io/select2/) tagging widgets which allow for the easy lookup of entities and establishing relations with those.  In the sample application the [FAST](http://fast.oclc.org/searchfast/) web service is used to lookup skos:Concepts.

 * [HTML5 boilerplate](http://www.initializr.com/try) and is repsonsive, which makes it mobile friendly as is.

##Use cases - what could I do with this?

 * create a "VIVO manager"-type application that allows researchers to manager and update [VIVO](http://vivoweb.org) research profiles.

 * create a mobile or table application that allows for straightforward editing of a subset of triple store data by end users.

 * as a data curating or cleaning tool.  SPARQL queries could pull problematic data from your triple-store and the built in widgets (or new widgets) could be used by staff to clean or augment the data.

 * as an educational tool to learn more about SPARQL, ontologies and RDF.  Personal experience disclaimer: when you try to read and write RDF data directly, the learning happens hard but faster.

A a [presentation](https://www.youtube.com/watch?v=cMprPKBRCl4) is available on YouTube that highlights some of the functionality and motivations behind using an application like this to manage data in a triple store.

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

##Development

To make ready use of this application, you would need access to a [VIVO](http://github.com/lawlesst/vivo-vagrant) instance with [sample data](http://github.com/lawlesst/vivo-sample-data).

If you are interested in using it with other triple stores (Sesame seems to be a good candidate, Fuesiki with updates turned on too) or applications, use the bundled `VivoBackend` as an example for writing your own backend.  If you wanted to write your own backend class it would need an `add_remove` method that accepts a RDFLib graph of additions and subtractions.  That's it.  Again, this is for demonstration purposes so it will require some tinkering and original code to connect to a different backend.

