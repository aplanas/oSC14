#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (C) 2014 aplanas@suse.de
# Distribute under GLPv2 or GPLv3

from xml.etree import cElementTree as ET

from osc import cmdln
from osc.core import http_GET
from osc.core import makeurl


@cmdln.alias('vr')
def do_viewrequest(self, subcmd, opts, *args):
    """${cmd_name}: view the raw content of a request

    Usage:
       ${cmd_name} SR ...
           View the raw content of a request
    ${cmd_option_list}
    """
    apiurl = self.get_api_url()
    for sr in args:
        url = makeurl(apiurl, ['request', str(sr)])
        print http_GET(url).read()
    #root = ET.parse(http_GET(url)).getroot()
    #return self._check_repo_one_request(root, opts)

