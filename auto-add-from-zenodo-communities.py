import sys
from _github_utilities import create_branch, get_file_in_repository, get_issue_body, write_file, send_pull_request, get_pull_requests_count
import yaml
import os
import requests
import shutil
import pandas as pd
from datetime import datetime
import yaml

def main():
    """
    Main function to handle the process of retrieving Zenodo data and appending
    it to a YAML file in a GitHub repository.

    This function takes command-line arguments for the repository name and issue number,
    retrieves the issue body, checks if it's a valid Zenodo link, retrieves corresponding
    data, and appends it to a specified YAML file by creating a new branch and submitting
    a pull request.

    Returns
    -------
    None
    """
    repository = "haesleinhuepf/zenodo-bluesky-bob" #TODO sys.argv[1]
    if get_pull_requests_count(repository) > 0:
        print("Leaving because former PR not processed yet.")

    token = os.getenv('ZENODO_API_KEY')
    communities = ['nfdi4bioimage', 'gerbi', 'euro-bioimaging', 'neubias', 'bio-formats', 'globias', 'rdm4mic']

    yml_filename = "resources/records.yml"

    # read "database"
    branch = "" #TODO create_branch(repository)
    print("New branch:", branch)
    log = []
    new_data = []

    # old data
    df = load_dataframe("resources/")
    all_urls = str(df["url"].tolist())

    for community in communities:
        log.append(f"# {community}")
        log.append(f"https://zenodo.org/communities/{community}")
        # new data
        response = requests.get('https://zenodo.org/api/records',
                                params={'communities': community,
                                        'access_token': token})
        online_data = response.json()
        hits = online_data["hits"]["hits"]
        urls = [u["links"]["self_html"] for u in hits]


        # compare which new is not in old

        for url in urls:
            print(url)
            data = complete_zenodo_data(url)

            if isinstance(data["url"], str):
                data["url"] = [data["url"]]

            not_in_data_yet = True
            for u in data["url"]:
                if u in all_urls:
                    not_in_data_yet = False

            if not_in_data_yet:
                data['submission_date'] = datetime.now().isoformat()
                name = data["name"]
                log.append(f"* [{name}]({url})")
                new_data.append(data)

                # deal with entries listed in multiple communities
                all_urls = all_urls + "\n" + "\n".join([u for u in data["url"]])
                break
        break

    # save data in repository
    #TODO zenodo_yml = yaml.dump(new_data)
    #TODO file_content = get_file_in_repository(repository, branch, yml_filename).decoded_content.decode()
    #TODO print("yml file content length:", len(file_content))
    # save back to github
    #TODO write_file(repository, branch, yml_filename, file_content, "Add entries from " + ", ".join(communities))
    log = "\n".join(log)
    #TODO res = send_pull_request(repository, branch, "Add content from communities: " + ", ".join(communities), f"Added contents:\n{log}")
    #TODO print("Done.", res)
    
    # save data in local file
    file_content = read_yaml_file(yml_filename)
    if file_content["resources"] is None:
        file_content["resources"] = new_data
    else:
        file_content["resources"] += new_data
    write_yaml_file(yml_filename, file_content)





def load_dataframe(directory_path):
    """
    Returns all contents (collected from all yml files) in a pandas DataFrame
    """
    import pandas as pd
    content = all_content(directory_path)

    if len(content['resources']) == 0:
        return pd.DataFrame({
            "url":[]
        })
    
    return pd.DataFrame(content['resources'])


def all_content(directory_path):
    """
    Go through all folders and yml files, and collect all content in a list of dictionaries.
    """
    import os
    content = {'resources':[]}
    for filename in os.listdir(directory_path):
        if filename.endswith('.yml'):
            #print("Adding", filename)
            new_content = read_yaml_file(os.path.join(directory_path, filename))  # Corrected line
            if new_content['resources'] is not None:
                content['resources'] = content['resources'] + new_content['resources']
    return content


def read_yaml_file(filename):
    """Read a yaml file and return the content as dictionary of dictionaries"""
    import yaml
    with open(filename, 'r', encoding="utf8") as file:
        data = yaml.safe_load(file)
        
        if "url" in data.keys() and "zenodo" in str(data["url"]).lower():
            data["tags"].append("zenodo")
        
        return data


def write_yaml_file(file_path, data):
    """Saves data as yaml file to disk"""
    import yaml
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def complete_zenodo_data(zenodo_url):
    """
    Completes Zenodo data retrieval and structuring for inclusion in a YAML file.

    Parameters
    ----------
    zenodo_url : str
        The URL of the Zenodo record.

    Returns
    -------
    entry : dict
        A dictionary containing structured metadata and statistics
        fetched from the Zenodo record.
    """
    zenodo_data = read_zenodo(zenodo_url)
    entry = {}
    urls = [zenodo_url]

    if 'doi_url' in zenodo_data.keys():
        doi_url = zenodo_data['doi_url']

        # Add DOI URL to the URLs list if it's not already there
        if doi_url not in urls:
            urls.append(doi_url)
    entry['url'] = urls

    if 'metadata' in zenodo_data.keys():
        metadata = zenodo_data['metadata']
        # Update entry with Zenodo metadata and statistics
        entry['name'] = metadata['title']
        if 'publication_date' in metadata.keys():
            entry['publication_date'] = metadata['publication_date']
        if 'creators' in metadata.keys():
            creators = metadata['creators']
            entry['authors'] = [c['name'] for c in creators]
            entry['first_author'] = creators[0]['name']
        if 'license' in metadata.keys():
            entry['license'] = metadata['license']['id']


    return entry


def read_zenodo(record):
    """
    Retrieves meta-data from zenodo.org of a specified record.
    """
    import requests
    import json

    record = record.replace("https://zenodo.org/", "")
    record = record.replace("record/", "records/")
    url = "https://zenodo.org/api/" + record

    #print(url)
    
    # Download the file
    response = requests.get(url)
    data = response.json()
    return data


if __name__ == "__main__":
    main()
