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
        return

    token = os.getenv('ZENODO_API_KEY')
    communities = ['nfdi4bioimage', 'gerbi', 'euro-bioimaging', 'neubias', 'bio-formats', 'globias', 'rdm4mic']

    yml_filename = "resources/records.yml"

    # read "database"
    branch = create_branch(repository)
    print("New branch:", branch)
    log = []
    new_data = []

    # old data
    df = load_dataframe("resources/")
    all_urls = str(df["url"].tolist())

    for community in communities:
        header = f"# [{community}](https://zenodo.org/communities/{community})"

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
                #name = data["name"]


                # formulate bluesky post
                post = formulate_post(data["first_author"], data["name"], data["description"])
                data['bluesky_post'] = post

                if header is not None:
                    log.append(header)
                    header = None

                log.append(f"* {post} [{url}]({url})")

                # download first page of PDF
                filename = download_image_from_record(data["id"])
                if filename is not None:
                    data["bluesky_image"] = filename

                    # upload file to github
                    with open(filename, 'rb') as f:
                        file_content = f.read()
                        write_file(repository, branch, filename, file_content,
                                                                  "Added image for Zenodo record " + data["id"])
                else:
                    print("Could not make image from PDF")

                new_data.append(data)

                # deal with entries listed in multiple communities
                all_urls = all_urls + "\n" + "\n".join([u for u in data["url"]])
                #break
        #break

    if len(new_data) > 0:
        # save data in repository
        zenodo_yml = yaml.dump(new_data)
        file_content = get_file_in_repository(repository, branch, yml_filename).decoded_content.decode()
        print("yml file content length:", len(file_content))
        # save back to github
        write_file(repository, branch, yml_filename, file_content + zenodo_yml, "Add entries from " + ", ".join(communities))
        log = "\n".join(log)
        res = send_pull_request(repository, branch, "Add content from communities: " + ", ".join(communities), f"If you merge this pull-request, the following blusky posts about given zenodo records will be posted:\n{log}")
        print("Done.", res)

        # save data in local file
        file_content = read_yaml_file(yml_filename)
        if file_content["resources"] is None:
            file_content["resources"] = new_data
        else:
            file_content["resources"] += new_data
        write_yaml_file(yml_filename, file_content)
        print("Done2.")
    print("Bye.")

def formulate_post(first_author, name, description):
    from _llm_utilities import prompt_azure
    post_text = prompt_azure(f"""
Formulate a 100 character long tweet. 
The content should be about the most recent work by {first_author} et al. about '{name}' published on Zenodo. 
This is the abstract of the work: 
{description}

Now, formulate a 100 character short tweet, enthusiastically mentioning the author and summarizing the work.
""")
    return post_text


def download_image_from_record(record_id):
    """
    If the license is CC-BY 4.0, download the first file from a Zenodo record and save the first page as PNG. This does only work if it is a PDF file.

    Adepted from: https://github.com/nfDI4BIOIMAGE/training/
    Licensed BSD-3 by Mara Lampert and Robert Haase
    """
    from pdf2image import convert_from_bytes
    from io import BytesIO
    import requests

    # Fetch record metadata
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Check if license is CC-BY-4.0
    license_info = data.get('metadata', {}).get('license', {}).get('id', '')
    print(f"License info from Zenodo: '{license_info}'")
    if license_info.lower() != "cc-by-4.0":
        print("Reuse not allowed: License is not CC-BY 4.0.")
        return None

    # Get the first PDF file's download link and file name
    for file_info in data['files']:
        if file_info['key'].endswith('pdf'):
            file_url = file_info['links']['self']
            file_name = file_info['key']

            # Download the file content
            response = requests.get(file_url)
            response.raise_for_status()
            file_content = BytesIO(response.content)

            # Check file extension and convert based on that
            file_extension = os.path.splitext(file_name)[1].lower()
            date = datetime.now().strftime("%Y%m%d")

            if file_extension == '.pdf':
                # Convert first page of PDF to PNG
                pages = convert_from_bytes(file_content.getvalue())
                img = pages[0]
                img = resize_image(img, height=500)
                filename = f'images/{date}_first_page_{record_id}.png'
                img.save(filename, 'PNG')
                print("First page of PDF saved as PNG.")
                return filename

            else:
                print(f"Unsupported file type: {file_extension}")

    return None


def resize_image(image, height):
    """
    Resize the image to the specified height while maintaining aspect ratio.

    Parameters
    ----------
    image : PIL.Image.Image
        The image to resize.
    height : int
        The desired height in pixels.

    Returns
    -------
    PIL.Image.Image
        The resized image.
    """
    from PIL import Image

    aspect_ratio = image.width / image.height
    new_width = int(aspect_ratio * height)
    return image.resize((new_width, height), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    main()
