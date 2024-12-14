# zenodo-bluesky-bob

This repository contains code that checks a selection of Zenodo Communities for new records being published. It will then post about them on [bluesky](https://bsky.app/). The posts are moderated using Github's Pull-Requests/Review mechanism. Under the hood we are using large language models via [Github Models Marketplace](https://github.com/marketplace) and the [atproto API](https://github.com/MarshalX/atproto). 
It runs in the github CI using daily [scheduled cron jobs](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule).

## Installation

To run this under your own account, you need clone the repository, activate Github actions and configure three secrets in your repository settings:
* `BLUESKY_API_KEY`
* `BLUESKY_USERNAME`
* `GH_MODELS_API_KEY`

## Contributing

Feedback and contributions are welcome! Just open an issue and let's discuss before you send a pull request. 

## Acknowledgements

We acknowledge the financial support by the Federal Ministry of Education and Research of Germany and by Sächsische Staatsministerium für Wissenschaft, Kultur und Tourismus in the programme Center of Excellence for AI-research „Center for Scalable Data Analytics and Artificial Intelligence Dresden/Leipzig", project identification number: ScaDS.AI
