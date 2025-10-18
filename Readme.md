# Installation Setup & Instructuions

## Requirements Installation

``` pip install -r requirements.txt ```

## Environment variables needed

Change the ```.env.example`` to ``.env```

``` LANGSMITH_PROJECT=ChatBot ```

``` LANGSMITH_API_KEY= # Get this from https://smith.langchain.com/ ```

``` OPENROUTER_API_KEY= YOUR_API_KEY```

``` REDIS_URL= YOUR-URL```

```MESSAGE_EXPIRY_SECONDS=300 ```

```TRIGGER_OFFSET_MINUTES=2 # Trigger analyzer 5 minutes before Redis expiry```

```SCHEDULER_INTERVAL_SECONDS=60 # How often scheduler checks for expiring sessions```

```MONGO_CONNECTION_URL= YOU-URL```

## Run the Server

``` langgraph dev  # For the chat bot server```

``` start_chedular.sh # For the redis auto summarization trigger```


# Testing

## Prompts Path

- prompts/ ---> companion & journal

## LLM Model

- config/llm.py
