# Copyright (C) 2014  Jamie Duncan (jduncan@redhat.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# File Name : changelogup.py
# Creation Date : 06-07-2014
# Created By : Jamie Duncan
# Last Modified : Sun 08 Jun 2014 11:12:19 AM EDT
# Purpose : for converting a git log stanza into a usable spec file changelog

import subprocess
import csv
from dateutil.parser import parse
from optparse import OptionParser
import os

#################################
#
# Python Module Requirement
# python-dateutil
#
##################################

class InvalidRepositoryError(Exception):
    pass

class NoGitTagsError(Exception):
    pass

class CLData:

    def __init__(self, options):

        self.t_start = options.t_start  #start tag
        self.t_end = options.t_end    #end tag, defaults to 'HEAD'
        self.search_term = options.search_term  #option search term to limit commit output
        self.repo = options.repo    #git repo directory to run against - defaults to curr working directory

        self._checkRepository()
        self._checkTags()

    def _checkRepository(self):
        if not os.path.isdir(os.path.join(self.repo, '.git')):
            raise InvalidRepositoryError("%s Does Not Appear to be a Valid git Repository" % self.repo)

    def _checkTags(self):
        #the logic here: if you don't have any tagged releases you should not be creating a spec file.

        git_command = 'git tag'
        cl_raw = subprocess.Popen(git_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.repo)

        tags = cl_raw.stdout.readlines()
        if len(tags) == 0:
            raise NoGitTagsError("The Repository Does Not Seem To Have any Tags Created. Please Verify.")

    def _formatDate(self, date):
        #returns the date in the proper format for a changelog in a spec file

        return parse(date).strftime('%a %b %d %Y')

    def _formatRelease(self, tag):
        # takes the decoration value and figures out if it's a new tag or not
        # if it's a new tag it takes it and prints out the full changelog entry
        # if it's not it just prints the commit line
        new_release = False
        if 'HEAD' in tag:
            if 'tag' in tag:
                tag = "- %s" % tag.split(':')[1].strip(' ()').split(',')[0] 
            else:
                tag = "- %s" % 'HEAD:UNRELEASED'
            new_release = True
        if 'tag' in tag:
            tag = "- %s" % tag.split(':')[1].strip(' ()')
            new_release = True

        return new_release,tag

    def _getGitLog(self):
        #grabs the raw git log data from the given repo

        git_command = 'git --no-pager log %s..%s --pretty --format=\'%%cD,%%cn,%%ce,%%h,"%%s","%%d"\'' % (self.t_start, self.t_end)
        if self.repo:
            cl_raw = subprocess.Popen(git_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.repo)
        else:
            cl_raw = subprocess.Popen(git_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return cl_raw.stdout.readlines()

    def formatChangeLog(self):

        data = self._getGitLog()
        a = csv.reader(data)
        for row in a:
            r_check,release = self._formatRelease(row[6])
            if r_check:
                print "\n* %s %s <%s> %s\n- %s =%s" % (self._formatDate(row[1]),row[2],row[3],release,row[4],row[5])
            else:
                if self.search_term:    #if we want to limit the output to lines with a certain string in the comment
                    if self.search_term in row[5]:
                        print "- %s : Commit %s" % (row[5],row[4])
                else:   #if we want all of the commits - no search term given
                    print "- %s : Commit %s" % (row[5],row[4])