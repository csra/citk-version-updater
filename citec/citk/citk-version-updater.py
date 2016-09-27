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
from collections import OrderedDict
import getpass
from git import *
from git.objects.base import *
import json
import os
from os.path import expanduser
import shutil
from termcolor import colored
    

#define
class Version(object):
    def __init__(self, major, minor, patch, build, release_type, tag):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build
        self.release_type = release_type
        self.tag = tag

if __name__ == "__main__":
    
    # pre init
    project_name = "?"
    project_file_name = "?"
    repo = None
    distribution_name = ""
    version_to_force = ""
    verbose_flag = False
    
    try:
        # init
        citk_path = expanduser("~") + "/workspace/csra/citk"
        project_name = str(os.path.relpath(".", ".."))

        # parse command line
        parser = argparse.ArgumentParser(description='Script upgrades te given project within the distribution file.')
        parser.add_argument("--project", default=project_name, help='The name of the project to apply the version upgrade.')
        parser.add_argument("--citk", default=citk_path, help='Path to the citk project which contains the project and distribution descriptions.')
        parser.add_argument("--distribution", default=distribution_name, help='The name of the distribution to apply the version upgrade.')
        parser.add_argument("--version", default=version_to_force, help='Can be used to force the version update to the given project version.')
        parser.add_argument("-v", default=verbose_flag, help='Enable this verbose flag to get more logging and exception printing during application errors.', action='store_true')
        args = parser.parse_args()
        project_name = args.project
        citk_path = args.citk
        distribution_name = args.distribution
        version_to_force = args.version
        verbose_flag = args.v
        
        # post init
        project_file_name = citk_path + '/projects/' + project_name + ".project"
        tmp_repo_directory = "/tmp/" + str(getpass.getuser()) + "/" + project_name
        distribution_file_uri = citk_path + "/distributions/" + distribution_name + ".distribution"
        distribution_tmp_file_uri = citk_path + "/distributions/." + distribution_name + ".distribution.tmp"
        
        # load and process
        with open(project_file_name, "r+") as project_file:
            
            data = json.load(project_file, object_pairs_hook=OrderedDict, encoding="utf-8")
            
            # load repo
            try:
                #print ("cache repo " + colored(data["variables"]["repository"], 'blue') + " into " + colored(tmp_repo_directory, 'blue'))
                if os.path.exists(tmp_repo_directory):
                    shutil.rmtree(tmp_repo_directory)
                repo = Repo.clone_from(data["variables"]["repository"], tmp_repo_directory)
                assert not repo.bare
            except Exception as ex:
                print("project repository entry could not found in project description " + colored(project_file_name, 'red'))
                if ex.message:
                    print("error: " + ex.message)
                    if verbose_flag:
                        print (ex)
                exit(233)

            # count existing branches
            if "branches" not in data["variables"]:
                branch_counter = 0
            else:
                branch_counter = len(data["variables"]["branches"])
            
            # remove existing branches
            data["variables"]["branches"] = []
            
            # store branches
            for branch_type in repo.refs:
                
                # filter local branches
                if not branch_type.is_remote():
                    continue
                    
                # filter head
                if branch_type.remote_head == "HEAD":
                    continue
                    
                branch = str(branch_type.remote_head)
                data["variables"]["branches"].append(branch)
            
            # sort branches
            data["variables"]["branches"].sort()
            
            # count existing tags
            if "tags" not in data["variables"]:
                tag_counter = 0
            else:
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
            project_file.write(json.dumps(data, sort_keys=False, indent=4, separators=(',', ': '), encoding="utf-8"))

        branch_counter = len(data["variables"]["branches"]) - branch_counter;
        tag_counter = len(data["variables"]["tags"]) - tag_counter;
        if branch_counter != 0:
            print("branch[" + str(branch_counter) + "] of project " + colored(project_name, 'green') + " updated in " + colored(project_file_name, 'blue') + "!")
        if tag_counter != 0:
            print("tags[" + str(tag_counter) + "] of project " + colored(project_name, 'green') + " updated in " + colored(project_file_name, 'blue') + "!")
    except Exception as ex:
        print("versions [branches|tags] of project " + colored(project_name, 'red') + " not updated in " + colored(project_file_name, 'blue') + "!")
        if ex.message:
            print("error: " + ex.message)
            if verbose_flag:
                print (ex)
        exit(1)

    # check if forced version is available
    if version_to_force:
        forced_version_verified = False
        for tag_type in repo.tags:
            if version_to_force == str(tag_type):
                forced_version_verified = True
        for branch_type in repo.refs:
            # filter local branches
            if not branch_type.is_remote():
                continue
                
            # filter head
            if branch_type.remote_head == "HEAD":
                continue
                
            if version_to_force == str(branch_type.remote_head):
                forced_version_verified = True
        if not forced_version_verified:
            print("error: the forced version " + colored(version_to_force, 'red') + " is not available for " + colored(project_name, 'blue'))
            exit(1);        
    
    # check if distribution updated is needed
    if not distribution_name:
        print("skip project upgrade within distribution because no distribution was defined!")
        shutil.rmtree(tmp_repo_directory)
        exit(0)
    
    if version_to_force:
        # force version
        selected_version = version_to_force
    else:
        if len(repo.tags) == 0:
            print("error: " + colored("no tags", 'red') + " available for project " + colored(project_name, 'blue'))
            exit(22)
        
        # dectect version
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
            
            if len(versionSplit) >= 4:
                build_number = int(versionSplit[3])
            else:
                build_number = None

            if len(tagSplit) > 1:
                releaseType = tagSplit[1]
            else:
                releaseType = "stable"

            #print("detected: major[" + str(major_version) + "] minor[" + str(minor_version) + "] patch[" + str(patch_version) + "] type[" + str(releaseType) + "]")

            current_tag = Version(major_version, minor_version, patch_version, build_number, releaseType, tag)

            try:
                selected_tag
            except NameError:
                selected_tag = current_tag
                continue
            else:
                if current_tag.major > selected_tag.major:  
                    selected_tag = current_tag
                    continue
                elif current_tag.major < selected_tag.major:
                    continue

                if current_tag.minor > selected_tag.minor:  
                    selected_tag = current_tag
                    continue
                elif current_tag.minor < selected_tag.minor:
                    continue

                if current_tag.patch > selected_tag.patch:  
                    selected_tag = current_tag
                    continue
                elif current_tag.patch < selected_tag.patch:
                    continue
                    
                if build_number:
                    if current_tag.build > selected_tag.build:  
                        selected_tag = current_tag
                        continue
                    elif current_tag.build < selected_tag.build:
                        continue

                if not "rc" in current_tag.release_type and "rc" in selected_tag.release_type:
                    selected_tag = current_tag
                    continue
                elif not "beta" in current_tag.release_type and "beta" in selected_tag.release_type:
                    selected_tag = current_tag
                    continue
                elif not "alpha" in current_tag.release_type and "alpha" in selected_tag.release_type:
                    selected_tag = current_tag
                    continue
        if not selected_tag.tag:
            print("error: " + colored("no valid tags", 'red') + " available for project " + colored(project_name, 'blue'))
            exit(23)
        selected_version = selected_tag.tag
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
                    if context[1] == project_name:
                        # prevent formatting
                        size_diff = len(context[3]) - len(selected_version)

                        context[2] = "," + " " * (len(context[2]) -1 + size_diff)

                        # verify current version
                        if context[3] == selected_version:
                            print(colored(project_name, 'blue') + " is already " + colored("up-to-date", 'green') + " within " + colored(distribution_name, 'blue'))
                            exit(0)

                        # upgrade
                        print("upgrade " + project_name + " version from " + colored(context[3], 'blue') + " to " + colored(selected_version, 'green'))
                        context[3] = selected_version
                        line = '"'.join(context)
                        project_found = True
                tmpFile.write(line)

    if not project_found:       
        print("project " + colored(project_name, 'blue') + " skipped! " + colored("Entry not found", 'yellow') + " in " + colored(distribution_file_uri, 'blue'))
        exit(0)

    # write back and cleanup
    shutil.rmtree(tmp_repo_directory)
    shutil.move(distribution_tmp_file_uri, distribution_file_uri)
    
                   
                



