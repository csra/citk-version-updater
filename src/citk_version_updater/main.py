#!/usr/bin/env python2
#encoding: UTF-8

###################################################################
#                                                                 #
# Copyright (C) 2016 - 2017 Divine Threepwood                     #
#                                                                 #
# File   : main.py                                #
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
import os
from os.path import expanduser
import shutil
from termcolor import colored
import coloredlogs, logging
import oyaml as yaml

coloredlogs.install()
_LOGGER = logging.getLogger(__name__)
_LOGGER.addHandler(logging.NullHandler())

#define
class Version(object):
    def __init__(self, major, minor, patch, build, release_type, tag):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build
        self.release_type = release_type
        self.tag = tag

def entry_point():
    exit(main())

def main(argv=None):
    
    # pre init
    project_name = "?"
    project_file_name = "?"
    repo = None
    distribution_name = ""
    version_to_force = ""

    try:
        # init
        citk_path = expanduser("~") + "/workspace/csra/citk"
        project_name = str(os.path.relpath(".", ".."))

        # setup command line
        parser = argparse.ArgumentParser(description='Script upgrades te given project within the distribution file.')
        parser.add_argument("--project", default=project_name, help='The name of the project to apply the version upgrade.')
        parser.add_argument("--citk", default=citk_path, help='Path to the citk project which contains the project and distribution descriptions.')
        parser.add_argument("--distribution", default=distribution_name, help='The name of the distribution to apply the version upgrade.')
        parser.add_argument("--version", default=version_to_force, help='Can be used to force the version update to the given project version.')
        parser.add_argument("--dry-run", help='This mode does not push modified changes to any git repositories.',
                            action='store_true')
        parser.add_argument("-v", help='Enable this verbose flag to get more logging and exception printing during application errors.', action='store_true')

        # print proper help screen if no arguments are given
        if len(argv) == 1:
            parser.print_help()
            return 1

        # parse command line
        args = parser.parse_args()

        project_name = args.project
        citk_path = args.citk
        distribution_name = args.distribution
        version_to_force = args.version

        # config logger
        if args.v:
            _LOGGER.setLevel(logging.DEBUG)
            coloredlogs.install(level='DEBUG', logger=_LOGGER)
            _LOGGER.debug('Debug log enabled.')
        else:
            _LOGGER.setLevel(logging.INFO)
        
        # post init
        project_file_name = os.path.join(citk_path, "projects", project_name + ".project")
        tmp_repo_directory = "/tmp/" + str(getpass.getuser()) + "/" + project_name
        distribution_file_uri = citk_path + "/distributions/" + distribution_name + ".distribution"
        distribution_tmp_file_uri = citk_path + "/distributions/." + distribution_name + ".distribution.tmp"

        # verify
        if not os.path.exists(distribution_file_uri):
            raise ValueError(
                "distribution " + colored(str(distribution_file_uri), 'red') + " does not exist!")

        # load and process
        with open(project_file_name, "r+") as project_file:
            
            data = yaml.load(project_file)
            #data = yaml.load(project_file, object_pairs_hook=OrderedDict, encoding="utf-8")

            # load repo
            try:
                _LOGGER.debug("cache repo " + colored(data["variables"]["repository"], 'blue') + " into " + colored(tmp_repo_directory, 'blue'))
                if os.path.exists(tmp_repo_directory):
                    shutil.rmtree(tmp_repo_directory)
                repo = Repo.clone_from(data["variables"]["repository"], tmp_repo_directory)
                assert not repo.bare
            except Exception as ex:
                _LOGGER.info("project repository entry could not found in project description " + colored(project_file_name, 'red'))
                if ex.message:
                    _LOGGER.error(colored("ERROR", 'red') + ": " + ex.message)
                    _LOGGER.debug(ex, exc_info=True)
                return 233

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
                    
                # filter origin refs
                if branch_type.remote_head.startswith("origin"):
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
        if not args.dry_run:
            with open(project_file_name, "w") as project_file:
                project_file.write(yaml.dump(data, allow_unicode=True, default_flow_style=False, encoding="utf-8"))

        branch_counter = len(data["variables"]["branches"]) - branch_counter
        tag_counter = len(data["variables"]["tags"]) - tag_counter
        if branch_counter != 0:
            _LOGGER.info("update " + colored(str(branch_counter), 'green') + " branch" + ("" if branch_counter == 1 else "s") + " of project " + colored(project_name, 'green') + " in " + colored(project_file_name, 'blue') + "!")
        if tag_counter != 0:
            _LOGGER.info("update " + colored(str(tag_counter), 'green') + " tag" + ("" if tag_counter == 1 else "s") + " of project " + colored(project_name, 'green') + " in " + colored(project_file_name, 'blue') + "!")
    except Exception as ex:
        _LOGGER.info("versions [branches|tags] of project " + colored(project_name, 'red') + " not updated in " + colored(project_file_name, 'blue') + "!")
        if ex.message:
            _LOGGER.error(colored("ERROR", 'red') + ": " + ex.message)
            _LOGGER.debug(ex, exc_info=True)
        return 1

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
        if not args.dry_run and not forced_version_verified:
            _LOGGER.error(colored("ERROR", 'red') + ": the forced version " + colored(version_to_force, 'red') + " is not available for " + colored(project_name, 'blue'))
            return 1
    
    # check if distribution updated is needed
    if not distribution_name:
        _LOGGER.info("skip project upgrade within distribution because no distribution was defined!")
        shutil.rmtree(tmp_repo_directory)
        return 0
    
    if version_to_force:
        # force version
        selected_version = version_to_force
    else:
        if len(repo.tags) == 0:
            _LOGGER.error(colored("ERROR", 'red') + ": " + colored("no tags", 'red') + " available for project " + colored(project_name, 'blue'))
            return 22
        
        # dectect version
        for tag_type in repo.tags:
            tag = str(tag_type)
            # skip if non regular version
            if not tag.startswith('v'):
                _LOGGER.debug("skip tag[" + tag + "] because it starts not with letter v")
                continue

                _LOGGER.debug("## found: " + tag)
            tagSplit = tag.split('-')
            versionSplit = tagSplit[0].split('.')
            major_version = int(versionSplit[0].replace("v", ""))

            if len(versionSplit) >= 2:
                minor_version = int(versionSplit[1])
            else:
                minor_version = 0

            if len(versionSplit) >= 3:
                patch_version = int(versionSplit[2])
            else:
                patch_version = 0
            
            if len(versionSplit) >= 4:
                build_number = int(versionSplit[3])
            else:
                build_number = None
            
            if len(tagSplit) > 1:
                releaseType = tagSplit[1]
            else:
                releaseType = "stable"

            _LOGGER.debug("detected: major[" + str(major_version) + "] minor[" + str(minor_version) + "] patch[" + str(patch_version) + "] type[" + str(releaseType) + "]")

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
            _LOGGER.error(colored("ERROR", 'red') + ": " + colored("no valid tags", 'red') + " available for project " + colored(project_name, 'blue'))
            return 23
        selected_version = selected_tag.tag
    project_found = False

    # update version in distribution file
    with open(distribution_tmp_file_uri, 'w') as tmpFile:
        _LOGGER.debug("detect projects...")
        with open(distribution_file_uri) as distributionFile:
            for line in distributionFile.readlines():
                if project_name in line:
                    _LOGGER.debug("found project :   " + str(line))
                    context = line.split('@')

                    # verify project name
                    if str(context[0]).startswith("- " + project_name):
                        # prevent formatting
                        #size_diff = len(context[3]) - len(selected_version)

                        #context[2] = "," + " " * (len(context[2]) -1 + size_diff)

                        # verify current version
                        if context[1] == selected_version+ "\n":
                            _LOGGER.info(colored(project_name, 'blue') + " is already " + colored("up-to-date", 'green') + " within " + colored(distribution_name, 'blue'))
                            return 0

                        # upgrade
                        _LOGGER.info("upgrade " + project_name + " version from " + colored(str(context[1]).replace("\n", ""), 'blue') + " to " + colored(selected_version, 'green'))
                        context[1] = selected_version + "\n"
                        line = '@'.join(context)
                        project_found = True
                tmpFile.write(line)

    if not project_found:
        _LOGGER.debug("project " + colored(project_name, 'blue') + " skipped! " + colored("Entry not found", 'yellow') + " in " + colored(distribution_file_uri, 'blue'))
        return 0

    # write back and cleanup
    if os.path.exists(tmp_repo_directory):
        shutil.rmtree(tmp_repo_directory)

    if not args.dry_run:
        shutil.move(distribution_tmp_file_uri, distribution_file_uri)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv))
                   
                



