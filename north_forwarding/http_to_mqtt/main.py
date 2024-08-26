
from fastapi import FastAPI
from pydantic import BaseModel


class FlegdeMessage(BaseModel):
    asset: str
    readings: dict
    timestamp: str


app = FastAPI()


def handle_fledge_messages(messages):
    print(f'{len(messages)=}')
    # print(f'{messages[0]=}')
    for message in messages:
        ...
        # print(message)


@app.post("/")
async def root(messages: list[FlegdeMessage]):
    handle_fledge_messages(messages)
    # return {"message": "Hello World"}
    # return [_ for _ in messages]
    return {}
"""
  {
    "asset": "randomwalk",
    "readings": {
      "randomwalk": 97
    },
    "timestamp": "2024-08-26T16:37:16.777354Z"
  },
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)



