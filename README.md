# WordSpark-Generator
WordSpark: Word-to-Story Generator

Words to Story is a web app for generating short stories with an OpenAI-compatible language model.
Choose at least 10 of the 30 available words and a genre (Comedy or Horror). Generated stories use
the selected words, are limited to 200 words, and are saved to PostgreSQL.

## Requirements

- Python and the packages in `requirements.txt`
- PostgreSQL with a database named `wordstory`
- An API key for the configured language-model provider

## Setup

Run these commands from the `story` directory:

1. Create the database:

   ```text
   create database wordstory
   ```

2. Install dependencies:

   ```text
   pip install -r requirements.txt
   ```

3. Set the API key and PostgreSQL connection string:

   ```text
   LLM_API_KEY=your-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/wordstory
   ```


## Run

Start the backend:

```text
uvicorn backend.main:app --reload
```

In a second terminal, also in the `story` directory, start the frontend:

```text
streamlit run frontend/app.py
```

Open the local URL printed by Streamlit. On backend startup,
the app creates its tables and seeds the 30 available words if needed.

## Story generation

When generating a story, the app retrieves up to three of the most recently saved stories from
PostgreSQL that match the selected genre. These stories are provided to the language model as
style examples for the new story. Stories from the other genre are not used as examples.
