# BorgNetzWerk / tools
Welcome to the BorgNetzWerk superproject! This repository contains all currently existing and future submodules for the project.

## Getting Started
Getting Started
To get started with the BorgNetzwerk project, you can either use the command line or the "Git Desktop" app.

### Command Line
1. You'll need to have [Git](https://git-scm.com/) installed on your machine. Once you have Git set up, you can clone the repository by running the following command:

```
git clone https://github.com/borgnetzwerk/borgnetzwerk.git
```

2. This will create a copy of the superproject repository on your local machine. You can then navigate into the repository by running:

```
cd borgnetzwerk
```

### Git Desktop App
1. Download and install the [Git Desktop](https://desktop.github.com/) app on your machine.
2. Once you have the app installed, open it and select "Clone a repository" from the File menu.
3. In the "Clone a Repository" window, enter the URL of the BorgNetzwerk superproject repository: "https://github.com/borgnetzwerk/borgnetzwerk" and select a local folder where you want to store the cloned repository.
4. Click "Clone" to start the cloning process. Once the cloning is done, the superproject repository will be available on your local machine in the selected folder.
## Execution order
The execution order of the submodules can be done in two ways:
1. Run one step for every item, then go to the next step
2. Run every step for one item, then go to the next item

# Submodules
## Information extraction
The information extraction submodules are designed to extract knowledge from various sources such as Youtube and Spotify.

### extract_from_html
This submodule is used to extract knowledge from Youtube and Spotify and can be used to feed into the following submodules:
- pytube_bot

### pytube_bot
This submodule is used to download meta-data, infos and captions for videos. It can also be used to do audio and can be fed into the following submodule:
- whisper

### whisper
This submodule is used to upcycle the audios from pytube_bot to written text.

## Information enhancement
The information enhancement submodules are designed to enhance the extracted information.

### spellcheck
This submodule is used to spellcheck the information.

### NLP
This submodule is used for natural language processing, not only for information enhancement, but also for extracting new knowledge by connecting text-based information.

#### Knowledge extraction
This submodule is used to extract new knowledge from the information by analyzing the text and identifying key concepts and relationships.

#### Lexikon
The lexikon is a list of all words used in the text, including their frequencies and how common they are in general lingo.

#### Lemmakon
This lexicon is a lexicon of lemmata, that groups the lexicon entries by their respective lemma, which makes it easy to identify patterns in the text.

#### Lemma per episode
This submodule uses the lemmacon by episode, so one can easily see what an episode was about by analyzing the lemmas used in that episode.

#### Keywords
The extracted noteworthy keywords. This submodule extracts the important keywords from the text, that are useful for understanding the main themes and concepts of the text.

### Similarity
This submodule is used to calculate the similarity between lemma-vectors and topic-vectors.

## publishing
The publishing submodules are an essential part of the BorgNetzwerk project, as they allow us to share our results with the community. We use different platforms to make the information accessible to a wide audience and to provide different ways for the community to interact with our project.

### obsidize
Our `obsidize` submodule allows us to publish our results to a local Obsidian.md, making it easy for the community to access and interact with the information. The Obsidian.md format is perfect for creating a personal knowledge base and allows users to create and link notes and organize information with ease.

### wikify
The `wikify` submodule allows us to publish our results to a MediaWiki under data.bnwiki.de, making it a great platform for collaboration. MediaWiki allows multiple users to contribute and edit the information, and also provides a version history of the changes made. This is great for creating a community-driven knowledge base and encourages engagement and collaboration.

### texify
With our `texify` submodule, we can publish our results to a local LaTeX project, which is perfect for creating high-quality documents. LaTeX is a typesetting system that allows users to create professional-looking documents with mathematical formulas, tables, and other advanced features. This is great for creating documents that will be shared with a professional audience, such as academic papers and reports.

We encourage the community to explore and interact with the information we publish on these platforms, and to reach out to us if they have any questions or feedback.

# Contributing
If you're interested in contributing to the BorgNetzwerk project, we'd love to have you! You can start by browsing through the open issues and picking one that you're interested in working on. If you have an idea for a new feature or a bug that you'd like to report, please open a new issue so we can discuss it. Once you're ready to start working on an issue, you can create a fork of the repository and submit a pull request when you're finished.

## IDEAS
This section is dedicated to listing and discussing ideas for new features and improvements for the BorgNetzwerk project.

- **Work in Progress**: These are ideas that are currently being developed or tested and are not yet ready to be implemented as submodules.
- **Suggestions**: These are ideas that have been suggested by the community or other contributors and are being considered for implementation.
- **Feature Requests**: These are specific features that have been requested by users and are being considered for implementation.
    - Read text from screen: a submodule that is able to extract text present in the video, not the audio track
    - Process images: a submodule that is able to compare videos that look similar, use similar images or styles

If you have an idea for a new feature or improvement, please feel free to open an issue in the repository to discuss it.

## Questions or Feedback
If you have any questions or feedback about the BorgNetzwerk project, please don't hesitate to reach out to us through through the issues section or the following channels:

- Contact Form: https://borgnetzwerk.de/kontakt/
- Discord: https://discord.com/invite/gATFDczS29
- YouTube: https://www.youtube.com/@BorgNetzWerk
- Twitch: https://www.twitch.tv/borgnetzwerk
