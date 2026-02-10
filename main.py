from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import deque
from typing import List

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production you can restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    reference: List[int]
    frames: int


def fifo(reference, frames):
    memory = deque()
    faults = 0
    hits = 0

    for page in reference:
        if page not in memory:
            faults += 1
            if len(memory) == frames:
                memory.popleft()
            memory.append(page)
        else:
            hits += 1

    return faults, hits


def lru(reference, frames):
    memory = []
    recent = {}
    faults = 0
    hits = 0

    for time, page in enumerate(reference):
        if page not in memory:
            faults += 1
            if len(memory) == frames:
                lru_page = min(recent, key=recent.get)
                memory.remove(lru_page)
                del recent[lru_page]
            memory.append(page)
        else:
            hits += 1

        recent[page] = time

    return faults, hits


def optimal(reference, frames):
    memory = []
    faults = 0
    hits = 0

    for i, page in enumerate(reference):
        if page not in memory:
            faults += 1
            if len(memory) == frames:
                future = {}
                for m in memory:
                    if m in reference[i+1:]:
                        future[m] = reference[i+1:].index(m)
                    else:
                        future[m] = float('inf')
                page_to_replace = max(future, key=future.get)
                memory.remove(page_to_replace)
            memory.append(page)
        else:
            hits += 1

    return faults, hits


@app.post("/simulate")
def simulate(data: SimulationRequest):

    fifo_f, fifo_h = fifo(data.reference, data.frames)
    lru_f, lru_h = lru(data.reference, data.frames)
    optimal_f, optimal_h = optimal(data.reference, data.frames)

    return {
        "fifo": {"faults": fifo_f, "hits": fifo_h},
        "lru": {"faults": lru_f, "hits": lru_h},
        "optimal": {"faults": optimal_f, "hits": optimal_h}
    }
