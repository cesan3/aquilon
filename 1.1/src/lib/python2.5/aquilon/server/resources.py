#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
'''The main class here is ResponsePage, which contains all the methods
for implementing the various aq commands.

To implement a command, define a transport for it in input.xml and
then add a command_<name>[_trigger] method to the ResponsePage class.
Any variables in the URL itself will be available as 
request.path_variable["varname"] where "varname" is the name of the
option.

The pages are built up at server start time based on the definitions in
the server's input.xml.  The RestServer class (which itself inherits
from ResponsePage for serving requests) contains this magic.  This
class builds out all the ResponsePage children as part of its __init__.

For any given ResponsePage, all methods (including all the command_
methods) are available, but only the expected methods for that relative
URL will be assigned to render_GET, render_POST, etc.  The rest will be
dormant.

Coming soon: the ResponsePage should provide some massaging for
incoming data, or at least handle requests for different output
formats consistently.  It can/should also provide some helpers for
those output formats.
'''

import re
import sys
import os
import xml.etree.ElementTree as ET
from base64 import b64decode
from tempfile import mkstemp

from twisted.application import internet
from twisted.web import server, resource, http, error
from twisted.internet import defer, utils
from twisted.python import log

from aquilon.server.exceptions_ import AuthorizationException, GitCommandException

class ResponsePage(resource.Resource):

    def __init__(self, broker, path, path_variable=None):
        self.path = path
        self.broker = broker
        self.path_variable = path_variable
        self.dynamic_child = None
        resource.Resource.__init__(self)
        # FIXME: How does the client request a different format?
        self.formats = []
        for attr in dir(self):
            if not callable(attr):
                continue
            if not attr.startswith("format_"):
                continue
            self.formats.append(attr[7:])

    def getChild(self, path, request):
        """Typically in twisted.web, a dynamic child would be created...
        dynamically.  However, to make the command_* mappings possible,
        they were all created at start time.

        This is an issue because the path cannot be handed to the
        constructor for it to deal with variable path names.  Instead,
        the request object is abused - the variable path names are
        crammed into it before handing back the child that is being
        requested.

        """

        if not self.dynamic_child:
            return resource.Resource.getChild(self, path, request)

        request.args[self.dynamic_child.path_variable] = [path]
        return self.dynamic_child

    def render(self, request):
        """This is just the default implementation from resource.Resource
        that checks for the appropriate method to delegate to.  This can
        be expanded out to do any default/incoming processing...

        """
        m = getattr(self, 'render_' + request.method, None)
        if not m:
            raise server.UnsupportedMethod(getattr(self, 'allowedMethods', ()))
        return m(request)

    def format(self, result, request):
        style = getattr(request, "output_format", "raw")
        formatter = getattr(self, "format_" + style, self.format_raw)
        return formatter(result, request)

    def format_raw(self, result, request):
        return str(result)

    # All of these wrap* functions should probably be elsewhere, and
    # change depending on what should go back to the client.
    def wrapRowsInTable(self, rp):
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for row in rp:
            data = [ "<td>%s</td>" % elem for elem in row ]
            retval.append( "<tr>\n" + "\n".join(data) + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        return str(retstr)

    # This is the wrong spot for this - but where should it go?  Should
    # it be in one of the Host* classes, which is then inherited by the
    # other?
    def wrapHostInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for h in rp:
            data = "<td>%s</td><td>%s</td>" % (h.id, h.name)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    # This is the wrong spot for this - but where should it go?
    def wrapAqdbTypeInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for o in rp:
            data = "<td>%s</td><td>%s</td>" % (o.id, o.type)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    # This is the wrong spot for this - but where should it go?
    def wrapLocationInTable(self, rp):
        print "Attempting results"
        retval = []
        if ( rp is None ):
            return "<p>No results.</p>"
        for loc in rp:
            data = "<td>%s</td><td>%s</td>" % (loc.id, loc.name)
            retval.append( "<tr>\n" + data + "\n</tr>\n" )
        retstr = "<table>\n" + "\n".join(retval) + "\n</table>\n"
        print "returning ", retstr
        return str(retstr)

    def wrapTableInBody(self, result):
        retval = """
        <html>
        <head><title>%s</title></head>
        <body>
        %s
        </body>
        </html>
        """ % (self.path, result)
        return str(retval)

    def finishRender(self, result, request):
        #print "about to write ", result
        request.setHeader('content-length', str(len(result)))
        request.write(result)
        request.finish()
        #print "All done"
        return

    def finishOK(self, result, request):
        """Ignore any results - usually empty for this - and finish"""
        # FIXME: Hack to get around client not understanding
        # zero-length response... Use explicit 0 when knc 1.3 exists.
        # Tried setting it explicitly...
        request.setHeader('content-length', 0)
        # Tried sending a "no content" response...
        #request.setResponseCode( http.NO_CONTENT )
        # For now, just send OK.
        #retval = "OK"
        #request.setHeader('content-length', len(retval))
        #request.write(retval)
        request.finish()
        return

    def finishError(self, request):
        request.setResponseCode( http.INTERNAL_SERVER_ERROR )
        # FIXME: Ditto from finishOK
        #retval = "FAILED"
        #request.setHeader('content-length', len(retval))
        #request.write(retval)
        request.setHeader('content-length', 0)
        request.finish()
        return

    # TODO: Something should go into both the logs and back to the client...
    def wrapError(self, failure, request):
        # FIXME: This should be overridden, looking for and trapping specific
        # exceptions.  Maybe this is left as a final check.
        print failure.getErrorMessage()
        failure.printDetailedTraceback()
        self.finishError(request)
        return failure

    def cb_git_command_finished(self, (out, err, code), request):
        """Raise an error for a non-zero return code."""
        log.msg("git command finished with return code %d" % code)
        log.msg("git command stdout: %s" % out)
        log.msg("git command stderr: %s" % err)
        if code != 0:
            raise GitCommandException("Git command failed with code: %d" % code)
        return out

    def cb_git_command_error(self, (out, err, signalNum), request):
        """Raise an error for a non-zero return code."""
        log.msg("git command exitted with signal %d" % signalNum)
        log.msg("git command stdout: %s" % out)
        log.msg("git command stderr: %s" % err)
        raise GitCommandException("Git command exitted with signal: %d"
                % signalNum)

    def command_show_host_all(self, request):
        """aqcommand: aq show host --all"""
        #print 'render_GET called'
        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/host")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.broker.dbbroker.showHostAll(session=True)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq show_host --all has not been implemented yet"
    
    def command_show_host_hostname(self, request):
        """aqcommand: aq show host --hostname=<host>"""
        name = request.args['hostname'][0]

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.broker.dbbroker.showHost(name, session=True)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq show_host --hostname has not been implemented yet"

    def command_add_host(self, request):
        """aqcommand: aq add host --hostname=<host>"""
        name = request.args['hostname'][0]
        #request.content.seek(0)

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "add", "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.broker.dbbroker.addHost(name, session=True)
        ## FIXME: Trap specific exceptions (host exists, etc.)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapHostInTable )
        #d = d.addCallback( self.wrapTableInBody )
        #d = d.addCallback( self.finishRender, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_host has not been implemented yet"

    def command_del_host(self, request):
        """aqcommand: aq del host --hostname=<host>"""
        name = request.args['hostname'][0]

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "del", "/host/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        #d = self.broker.dbbroker.delHost(name, session=True)
        ## FIXME: Trap specific exceptions (host exists, etc.)
        #d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.finishOK, request )
        #d = d.addErrback(log.err)
        #return server.NOT_DONE_YET
        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq del_host has not been implemented yet"

    def command_pxeswitch(self, request):
        """aqcommand: aq pxeswitch --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq pxeswitch has not been implemented yet"

    def command_assoc(self, request):
        """aqcommand: aq assoc --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq assoc has not been implemented yet"

    def command_reconfigure(self, request):
        """aqcommand: aq reconfigure --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq reconfigure has not been implemented yet"

    def command_cat_hostname(self, request):
        """aqcommand: aq cat --hostname=<host>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq cat --hostname has not been implemented yet"

    def command_cat_template(self, request):
        """aqcommand: aq cat --template=<template> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq cat --template has not been implemented yet"

    def command_add_domain(self, request):
        """aqcommand: aq add domain --domain=<domain>"""
        domain = request.args['domain'][0]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_domain has not been implemented yet"

    def command_del_domain(self, request):
        """aqcommand: aq del domain --domain=<domain>"""
        domain = request.args['domain'][0]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq del_domain has not been implemented yet"

    def command_add_template(self, request):
        """aqcommand: aq add template --name=<name> --domain=<domain>"""
        domain = request.args['domain'][0]
        template = request.args['name'][0]

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add_template has not been implemented yet"

    def command_get(self, request):
        """aqcommand: aq get"""

        # FIXME: Lookup the default domain.
        domain = "production"

        request.args["domain"] = [domain]

        return self.command_get_domain(request)

    def command_get_domain(self, request):
        """aqcommand: aq get --domain=<domain>"""
        domain = request.args['domain'][0]

        # FIXME: Lookup whether this server handles this domain
        # redirect as necessary.

        # FIXME: The server needs to have its name around somewhere...
        localhost = "quattorsrv"

        # FIXME: Return absolute paths to git?
        return "git clone 'http://%s/templates/%s/.git/%s' && cd '%s' && ( git checkout -b '%s' || true )" % (localhost, domain, domain, domain, domain)

    def decode_and_write(self, encoded):
        decoded = b64decode(encoded)
        (handle, filename) = mkstemp()
        # Write decoded to the filename
        return filename

    def command_put(self, request):
        """aqcommand: aq put --domain=<domain>"""
        bundle = request.args["bundle"][0]

        # FIXME: Lookup whether this server handles this domain
        # redirect as necessary.

        domaindir = self.broker.templatesdir + "/" + domain
        # FIXME: Check that it exists.

        #d = deferToThread(self.decode_and_write, bundle)
        #d = d.addCallback(lambda filename: utils.getProcessOutputAndValue(
        #    "/bin/sh", ["-c", "cd '%s/%s' && 
        #    d = utils.getProcessOutputAndValue("/bin/sh",
        #            ["-c", "cd '%s' && %s update server info"

        # FIXME: Code in progress here...

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq put has not been implemented yet"

    def command_deploy(self, request):
        """aqcommand: aq deploy --domain=<domain> --to=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq deploy has not been implemented yet"

    def command_manage(self, request):
        """aqcommand: aq manage --hostname=<name> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq manage has not been implemented yet"

    def command_sync(self, request):
        """aqcommand: aq sync --domain=<domain>"""

        # FIXME: Lookup the default domain.
        domain = "production"

        request.args["domain"] = [domain]

        return self.command_sync_domain(request)

    def command_sync_domain(self, request):
        """aqcommand: aq sync --domain=<domain>"""
        domain = request.args['domain'][0]

        # FIXME: Sanitize domain before it is used in commands.

        # FIXME: Lookup whether this server handles this domain
        # and redirect as necessary.
        # Presumably, that lookup will catch domains that do not
        # actually exist.

        # FIXME: Check whether the directory exists.
        domaindir = self.broker.templatesdir + '/' + domain

        d = utils.getProcessOutputAndValue("/bin/sh",
                ["-c", "cd '%s' && %s pull" % (domaindir, self.broker.git)])
        d = d.addCallbacks(self.cb_git_command_finished,
                self.cb_git_command_error,
                callbackArgs=[request], errbackArgs=[request])
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        d = d.addCallback(lambda _: utils.getProcessOutputAndValue("/bin/sh",
                ["-c", "cd '%s' && %s update server info"
                    % (domaindir, self.broker.git)]))
        d = d.addCallbacks(self.cb_git_command_finished,
                self.cb_git_command_error,
                callbackArgs=[request], errbackArgs=[request])
        # All went well... send client command.
        d = d.addCallback(lambda _: "git pull")
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(self.wrapError, request)
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET


    def command_show_location_types(self, request):
        """aqcommand: aq show location"""
        #print 'render_GET called'
        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/location")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.broker.dbbroker.showLocationType(session=True)
        d = d.addErrback(self.wrapError, request)
        #d = d.addCallback(self.wrapAqdbTypeInTable)
        #d = d.addCallback(self.wrapTableInBody)
        d = d.addCallback(self.format, request)
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET
    
    def command_show_location_type(self, request):
        """aqcommand: aq show location --type"""
        type = request.args['type'][0]
        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/location/%s" % type)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.broker.dbbroker.showLocation(session=True, type=type)
        d = d.addErrback(self.wrapError, request)
        #d = d.addCallback( self.wrapLocationInTable )
        #d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback(self.format, request)
        d = d.addCallback(self.finishRender, request)
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET
    
    def command_show_location_name(self, request):
        """aqcommand: aq show location --name=<location>"""
        type = request.args['type'][0]
        name = request.args['name'][0]

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.broker.dbbroker.showLocation(type=type, name=name,
                session=True)
        d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapLocationInTable )
        #d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback(self.format, request)
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def command_add_location(self, request):
        """aqcommand: aq add location --locationname=<location>"""
        type = request.args['type'][0]
        name = request.args['name'][0]

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "add", "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.broker.dbbroker.addLocation(name, session=True)
        # FIXME: Trap specific exceptions (location exists, etc.)
        d = d.addErrback( self.wrapError, request )
        #d = d.addCallback( self.wrapLocationInTable )
        #d = d.addCallback( self.wrapTableInBody )
        d = d.addCallback(self.format, request)
        d = d.addCallback( self.finishRender, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def command_del_location(self, request):
        """aqcommand: aq del location --locationname=<location>"""
        type = request.args['type'][0]
        name = request.args['name'][0]

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "del", "/location/%s" % name)
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        d = self.broker.dbbroker.delLocation(name, session=True)
        # FIXME: Trap specific exceptions (location exists, etc.)
        d = d.addErrback( self.wrapError, request )
        d = d.addCallback( self.finishOK, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def command_run_dummy_command(self, request):
        def _cb_command_output((out, err, code)):
            log.msg("echo finished with return code %d" % code)
            # FIXME: do stuff with err and code
            return out

        def _cb_command_error((out, err, signalNum)):
            # FIXME: do stuff with err and signalNum
            return out

        # Here's what is happening...
        # Set up a Deferred to run a process and get the output.
        d = utils.getProcessOutputAndValue("/bin/echo",
                [ "/bin/env && echo hello && sleep 1 && echo hi; echo bye" ] )
        # Set up callbacks to just return the stdout output
        d = d.addCallbacks(_cb_command_output, _cb_command_error)
        # Ignore the data being brought in (demo purposes, although
        # similar would happen in a real command chain... generally
        # we're not parsing output, just looking for a successful
        # command with the return code).
        # Create a new Deferred within the callback!  Twisted will
        # then run the results through this (existing) callback chain!
        d = d.addCallback(lambda _: utils.getProcessOutputAndValue(
                "/bin/echo",
                ["/bin/env && echo hello there && sleep 1 && echo bye"]))
        # Same callbacks as before - just return stdout
        d = d.addCallbacks(_cb_command_output, _cb_command_error)
        # Pass the output of *only* the second command (the first
        # one was thrown away) back to the client with finishRender.
        d = d.addCallback( self.finishRender, request )
        # Catch any uncaught expceptions and finish the request.
        d = d.addErrback( self.wrapError, request )
        d = d.addErrback(log.err)
        return server.NOT_DONE_YET

    def command_status(self, request):
        """aqcommand: aq status"""

        try:
            self.broker.azbroker.check(None, request.channel.getPrinciple(),
                    "show", "/")
        except AuthorizationException:
            request.setResponseCode( http.UNAUTHORIZED )
            return ""

        return self.format("OK", request)

    # FIXME: Probably going to change...
    def command_add_hardware(self, request):
        """aqcommand: aq add hardware --location=<location>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add hardware has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_model(self, request):
        """aqcommand: aq add model --os=<os> --model=<model> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add model has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_service(self, request):
        """aqcommand: aq add service --service=<service> --domain=<domain>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add service has not been implemented yet"

    # FIXME: Probably going to change...
    def command_add_service_instance(self, request):
        """aqcommand: aq add service --service=<service> --domain=<domain> --instance=<instance>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq add service --instance has not been implemented yet"

    # FIXME: Probably going to change...
    def command_bind_service(self, request):
        """aqcommand: aq bind service --service=<service> --hostname=<hostname>"""

        request.setResponseCode( http.NOT_IMPLEMENTED )
        return "aq bind service has not been implemented yet"


class BrokerInfo(object):
    """For now, simple container object.  This will probably be 
    initialized with a conf file at some point in the future, which could
    set up the dbbroker, azbroker, etc.
    
    """

    def __init__(self, dbbroker, azbroker):
        self.dbbroker = dbbroker
        self.azbroker = azbroker
        self.osuser = os.environ.get('USER')
        self.basedir = "/var/tmp/%s/quattor" % self.osuser
        self.profilesdir = "%s/web/htdocs/profiles" % self.basedir
        self.depsdir = "%s/deps" % self.basedir
        self.hostsdir = "%s/hosts" % self.basedir
        self.templatesdir = "%s/templates" % self.basedir
        self.default_domain = ".ms.com"
        self.git = "/ms/dist/fsf/PROJ/git/1.5.4.2/bin/git"
        self.htpasswd = "/ms/dist/elfms/PROJ/apache/2.2.6/bin/htpasswd"
        self.cdpport = 7777


class RestServer(ResponsePage):
    """The root resource is used to define the site as a whole."""
    def __init__(self, broker):
        ResponsePage.__init__(self, broker, '')

        # Regular Expression for matching variables in a path definition.
        varmatch = re.compile(r'^%\((.*)\)s$')

        BINDIR = os.path.dirname( os.path.realpath(sys.argv[0]) )
        tree = ET.parse( os.path.join( BINDIR, '..', 'etc', 'input.xml' ) )

        for command in tree.getiterator("command"):
            for transport in command.getiterator("transport"):
                if not command.attrib.has_key("name") \
                        or not transport.attrib.has_key("method") \
                        or not transport.attrib.has_key("path"):
                    continue
                name = command.attrib["name"]
                method = transport.attrib["method"]
                path = transport.attrib["path"]
                trigger = transport.attrib.get("trigger")
                container = self
                relative = ""
                # Traverse down the resource tree, container will
                # end up pointing to the correct spot.
                # Create branches and leaves as necessary, continueing to
                # traverse downward.
                for component in path.split("/"):
                    relative = relative + "/" + component
                    #log.msg("Working with component '" + component + "' of '" + relative + "'.")
                    m = varmatch.match(component)
                    # Is this piece of the path dynamic?
                    if not m:
                        #log.msg("Component '" + component + "' is static.")
                        child = container.getStaticEntity(component)
                        if child is None:
                            #log.msg("Creating new static component '" + component + "'.")
                            child = ResponsePage(self.broker, relative)
                            container.putChild(component, child)
                        container = child
                    else:
                        #log.msg("Component '" + component + "' is dynamic.")
                        path_variable = m.group(1)
                        if container.dynamic_child is not None:
                            #log.msg("Dynamic component '" + component + "' already exists.")
                            current_variable = container.dynamic_child.\
                                    path_variable
                            if current_variable != path_variable:
                                log.err("Could not use variable '"
                                        + path_variable + "', already have "
                                        + "dynamic variable '" 
                                        + current_variable + "'.")
                                # XXX: Raise an error if they don't match
                                container = container.dynamic_child
                            else:
                                #log.msg("Dynamic component '" + component + "' had correct variable.")
                                container = container.dynamic_child
                        else:
                            #log.msg("Creating new dynamic component '" + component + "'.")
                            child = ResponsePage(self.broker, relative,
                                                    path_variable=path_variable)
                            container.dynamic_child = child
                            container = child

                fullcommand = name
                if trigger:
                    fullcommand = fullcommand + "_" + trigger
                # If the command has not been implemented yet, the server
                # will bail out on startup with something like:
                # AttributeError: ResponsePage instance has no attribute
                #  'command_xxx'
                # Go create it, or fix the command/transport definition.
                mycommand = getattr(container, "command_" + fullcommand)
                rendermethod = "render_" + method.upper()
                if getattr(container, rendermethod, None):
                    # FIXME: Raise an Error, something has already been added
                    log.err("Already have a %s here at %s..." %
                            (rendermethod, container.path))
                #log.msg("Setting 'command_" + fullcommand + "' as '" + rendermethod + "' for container '" + container.path + "'.")
                setattr(container, rendermethod, mycommand)

        def _logChildren(level, container):
            for (key, child) in container.listStaticEntities():
                log.msg("Resource at level %d for %s [key:%s]"
                        % (level, child.path, key))
                _printChildren(level+1, child)
            if container.dynamic_child:
                log.msg("Resource at level %d for %s [dynamic]"
                        % (level, container.dynamic_child.path))
                _printChildren(level+1, container.dynamic_child)

        #_logChildren(0, self)

