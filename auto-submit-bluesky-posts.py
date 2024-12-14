import sys
from _github_utilities import create_branch, get_file_in_repository, get_issue_body, write_file, send_pull_request, get_pull_requests_count
from _data_utilities import load_dataframe, all_content, write_yaml_file, complete_zenodo_data, read_yaml_file
import yaml
import os
import requests
import shutil
import pandas as pd
from datetime import datetime
import yaml
from _bluesky_utilities import send_post

def main():
    repository = "haesleinhuepf/zenodo-bluesky-bob" #TODO sys.argv[1]
    yml_filename = "resources/records.yml"

    # read "database"
    posted_something = False
    data = read_yaml_file(yml_filename)
    for row in data["resources"]:
        keys = list(row.keys())
        if "bluesky_post" in keys and "bluesky_url" not in keys:
            link = row["url"]
            if isinstance(link, list):
                link = link[-1]

            message = row["bluesky_post"]
            print("Tweeting:", message, link)
            row["bluesky_url"] = send_post(message, link)
            posted_something = True

    if posted_something:
        write_yaml_file(yml_filename, data)
    
        # submit changes to Github
        branch = "main"
        file_content = get_file_in_repository(repository, branch, yml_filename).decoded_content.decode()
        
        # save back to github
        write_file(repository, branch, yml_filename, file_content, "Tweeted")
        print("Tweeting done")
    else:
        print("Nothing to tweet")


if __name__ == "__main__":
    main()
