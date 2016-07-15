#!/usr/bin/env python2
#encoding: UTF-8

###################################################################
#                                                                 #
# Copyright (C) 2016 Divine Threepwood                            #
#                                                                 #
# File   : screenservice.py                                       #
# Authors: Divine Threepwood (Marian Pohling)                     #
#                                                                 #
#                                                                 #
# GNU LESSER GENERAL PUBLIC LICENSE                               #
# This file may be used under the terms of the GNU Lesser General #
# Public License version 3.0 as published by the                  #
#                                                                 #
# Free Software Foundation and appearing in the file LICENSE.LGPL #
# included in the packaging of this file.  Please review the      #
# following information to ensure the license requirements will   #
# be met: http://www.gnu.org/licenses/lgpl-3.0.txt                #
#                                                                 #
###################################################################

# import
from __future__ import print_function
import argparse
from git import *
from git.objects.base import *
import os
import shutil
from termcolor import colored
import getpass
import json
from collections import OrderedDict
import json
    

#define
class Version(object):
    def __init__(self, major, minor, patch, release_type, tag):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.release_type = release_type
        self.tag = tag

if __name__ == "__main__":
    
    # pre init
    project_name = "?"
    project_file_name = "?"
    repo = None
    distribution_name = ""
    
    try:
        # init
        citk_path = "/home/" + str(getpass.getuser()) + "/workspace/csra/citk"
        project_name = str(os.path.relpath(".", ".."))

        # parse command line
        parser = argparse.ArgumentParser(description='Script upgrades te given project within the distribution file.')
        parser.add_argument("--project", default=project_name, help='The name of the project to apply the version upgrade.')
        parser.add_argument("--citk", default=citk_path, help='Path to the citk project which contains the project and distribution descriptions.')
        parser.add_argument("--distribution", default=distribution_name, help='The name of the distribution to apply the version upgrade.')
        args = parser.parse_args()
        project_name = args.project
        citk_path = args.citk
        distribution_name = args.distribution
        
        # post init
        project_file_name = citk_path+'/projects/'+project_name+".project"
        tmp_repo_directory = "/tmp/" + str(getpass.getuser()) + "/" +project_name
        distribution_file_uri = citk_path + "/distributions/" + distribution_name + ".distribution"
        distribution_tmp_file_uri = citk_path + "/distributions/." + distribution_name + ".distribution.tmp"
        
        # load and process
        with open(project_file_name, "r+") as project_file:    

            data = json.load(project_file, object_pairs_hook=OrderedDict)
            
            # load repo
            try:
                print ("cache repo "+colored(data["variables"]["repository"], 'blue')+" into " + colored(tmp_repo_directory, 'blue'))
                if os.path.exists(tmp_repo_directory):
                    shutil.rmtree(tmp_repo_directory)
                repo = Repo.clone_from(data["variables"]["repository"], tmp_repo_directory)
                assert not repo.bare
            except Exception as ex:
                print("project repository entry could not found in project description "+colored(project_file_name, 'red'))
                if ex.message:
                    print("error: "+ex.message)
                exit(233)

            tag_counter = len(data["variables"]["tags"])

            # remove existing tags
            data["variables"]["tags"] = []

            # store tags
            for tag_type in repo.tags:
                tag = str(tag_type)
                data["variables"]["tags"].append(tag)

            # sort tags
            data["variables"]["tags"].sort()

        # store back
        with open(project_file_name, "w") as project_file:
            project_file.write(json.dumps(data, sort_keys=False, indent=4, separators=(',', ': ')))

        tag_counter = len(data["variables"]["tags"]) - tag_counter;
        print("tags["+str(tag_counter)+"] of project " + colored(project_name, 'green') + " updated in "+colored(project_file_name, 'blue')+"!")
    except Exception as ex:
        print("tags of project " + colored(project_name, 'red') + " not updated in "+colored(project_file_name, 'blue')+"!")
        if ex.message:
            print("error: "+ex.message)
        exit(1)

    if not distribution_name:
        print("skip project upgrade within distribution because no distribution was defined!")
        shutil.rmtree(tmp_repo_directory)
        exit(0)
    

    for tag_type in repo.tags:
        tag = str(tag_type)
        # skip if non regular version
        if not tag.startswith('v'):
            print("skip tag:" + tag)
            continue

        #print("found: " + tag)
        tagSplit = tag.split('-')
        versionSplit = tagSplit[0].split('.')
        major_version = int(versionSplit[0].replace("v", ""))
        minor_version = int(versionSplit[1])
        patch_version = int(versionSplit[2])

        if len(tagSplit) > 1:
            releaseType = tagSplit[1]
        else:
            releaseType = "stable"

        #print("detected: major[" + str(major_version) + "] minor[" + str(minor_version) + "] patch[" + str(patch_version) + "] type[" + str(releaseType) + "]")

        currentTag = Version(major_version, minor_version, patch_version, releaseType, tag)

        try:
            latestTag
        except NameError:
            latestTag = currentTag
            continue
        else:
            if currentTag.major > latestTag.major:  
                latestTag = currentTag
                continue
            elif currentTag.major < latestTag.major:
                continue

            if currentTag.minor > latestTag.minor:  
                latestTag = currentTag
                continue
            elif currentTag.minor < latestTag.minor:
                continue

            if currentTag.patch > latestTag.patch:  
                latestTag = currentTag
                continue
            elif currentTag.patch < latestTag.patch:
                continue

            if not currentTag.release_type.contains("beta"):
                if latestTag.release_type.contains("beta"):
                    latestTag = currentTag
                    continue

    project_found = False

    # update version in distribution file
    with open(distribution_tmp_file_uri, 'w') as tmpFile:
        #print("detect projects...")
        with open(distribution_file_uri) as distributionFile:
            for line in distributionFile.readlines():
                #print("lines...")
                if project_name in line:

                    #print("found project :   " + str(line))
                    context = line.split('"')

                    # verify project name
                    if not context[1] == project_name:
                        # skip non project entry
                        continue

                    # prevent formatting
                    size_diff = len(context[3]) - len(latestTag.tag)

                    context[2] = "," + " " * (len(context[2]) -1 + size_diff)

                    # verify current version
                    if context[3] == latestTag.tag:
                        print(colored(project_name + " is already up-to-date!", 'green') + " within the in ")
                        exit(0)

                    # upgrade
                    print("upgrade " + project_name + " version from " + colored(context[3], 'blue') + " to " + colored(latestTag.tag, 'green'))
                    context[3] = latestTag.tag
                    line = '"'.join(context)
                    project_found = True
                tmpFile.write(line)

    if not project_found:       
        print("project " + colored(project_name, 'blue') + " skipped! " + colored("Entry not found", 'yellow') + " in " + colored(distribution_file_uri, 'blue'))
        exit(0)

    # write back and cleanup
    shutil.rmtree(tmp_repo_directory)
    shutil.move(distribution_tmp_file_uri, distribution_file_uri)
    
                   
                



