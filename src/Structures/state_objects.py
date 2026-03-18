from typing import TypedDict
from typing import Annotated
from src.Structures.pydantic_objects import FilteredNewsResponse,merge_filtered,FinalResult,merge_dicts

class GeneralState(TypedDict):
    category: str 
    preference: str 
    url:list
    config: dict
    filtered_cnt: Annotated[FilteredNewsResponse, merge_filtered]
    summary     : Annotated[dict, merge_dicts]
    final_output: FinalResult

class ReSummarize(TypedDict):
    items:list
    final_res: dict 
    retry_map:dict