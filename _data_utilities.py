
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
    entry = {"id": zenodo_data["id"]}
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
        if 'description' in metadata.keys():
            entry['description'] = remove_html_tags(metadata['description'])
        if 'creators' in metadata.keys():
            creators = metadata['creators']
            entry['authors'] = [c['name'] for c in creators]
            entry['first_author'] = creators[0]['name']
        if 'license' in metadata.keys():
            entry['license'] = metadata['license']['id']


    return entry


def remove_html_tags(text):
    """
    Clean HTML code and turn it into plain text.
    """
    import re
    cleaned_text = re.sub('<.*?>', '', text)
    return cleaned_text
    

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
    data["id"] = record.split("/")[-1]
    return data