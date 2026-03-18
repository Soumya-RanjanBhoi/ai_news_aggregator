from pydantic import BaseModel,Field,HttpUrl
from typing import List


class NewsItem(BaseModel):
    """Represents a single filtered news item returned by the agent."""
    title: str = Field(..., description="The attention-grabbing news headline")
    source: str = Field(..., description="The news source (e.g. bbci, espn, skysports)")
    url: str = Field(..., description="The full URL to the article")


class FilteredNewsResponse(BaseModel):
    """Top 4 filtered news items selected by the agent."""
    items: List[NewsItem] = Field(...,min_length=1,max_length=4,description="Exactly 4 most interesting news items"
    )

class SummaryStructure(BaseModel):
    """ This  is used for summary generation. """
    summary: str = Field(...,description="3-4 line summary of the given markdown text")

class FinalResultEntity(BaseModel):
    """ This is used to get final structured output"""
    category: str = Field(...,description="Category chosen by the user")
    preference : str = Field(...,description="Out of selected category which sport they prefer")
    url: HttpUrl = Field(...,description="url of the news")
    source: str =Field(...,description="Source of the news")
    summary: str = Field(...,description="summary of the news that are after filteration")

def merge_dicts(a: dict, b: dict) -> dict:
    """Merge two summary dicts together"""
    return {**a, **b}

def merge_filtered(a: FilteredNewsResponse, b: FilteredNewsResponse) -> FilteredNewsResponse:
    """Merge two FilteredNewsResponse objects together"""
    return FilteredNewsResponse(items=a.items + b.items)

class Re_Summarize(BaseModel):
    summary : str = Field(...,description='summary of the markdown text')


class FinalResult(BaseModel):
    details: List[FinalResultEntity]