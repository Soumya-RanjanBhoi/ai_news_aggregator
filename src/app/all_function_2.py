from src.Structures.pydantic_objects import *
from src.Structures.state_objects import * 
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from src.app.all_function_1 import workflow_1_function
from langchain_core.runnables import RunnableLambda,RunnableParallel
from firecrawl import Firecrawl
import os
from langgraph.graph import StateGraph,START,END
from dotenv import load_dotenv
from langchain_groq import ChatGroq

class Workflow2:
    def __init__(self):
        workflow1_obj = workflow_1_function()
        self.workflow1 = workflow1_obj.build_workflow()
        print("Workflow 1 builded")
        self.app =Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY",""))

        load_dotenv()


    @retry(stop=stop_after_attempt(5),wait=wait_exponential(multiplier=2, min=4, max=60),retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
        reraise=True)
    def invoke_with_retry(self,chain, input_data):
        """Invoke a chain with automatic retry on transient HTTP failures"""
        return chain.invoke(input_data) 
    

    def re_summarize(self,details, text):
        chat_model=ChatMistralAI(model="ministral-8b-2512")
        parser = PydanticOutputParser(pydantic_object=Re_Summarize)
        summ_prompt = PromptTemplate(
            template="""You are a precise summarization assistant.

            Your task:
            - Read the markdown text carefully
            - Ignore all formatting, symbols, and redundant content
            - Extract only the core, meaningful information
            - Write a clear and concise summary in exactly 2-3 sentences
            - Do NOT include opinions, filler phrases, or repetition
            - No explanation, no markdown.

            Text:
            {text} \n\n
            {format_instructions}
            """,
            input_variables=['text'],
            partial_variables={'format_instructions': parser.get_format_instructions()}
        )

        chain = summ_prompt | chat_model | parser 
        sum_res = self.invoke_with_retry(chain, {"text": text})
        
        return FinalResultEntity(
            category=details.category,
            preference=details.preference,
            url=details.url,
            title=details.title,
            source=details.source,
            summary=sum_res.summary,
            is_breaking=details.is_breaking,
            score=details.score
        )
    
    
    def run_workflow(self,items):
        if self.workflow1 !=None:
            result= self.workflow1.invoke({"category":items['category'],"preference":items['preference']})
            return result
        
        else :
            print("Error in building first Workflow")

    def run_parallel_workflow(self,state:ReSummarize):
        items = state['items']
        parallel_chain = {
            f"{item['category']}_{item['preference']}": RunnableLambda(
                lambda x, i=item: self.run_workflow(i)
            )
            for item in items
        }

        combined_chain = RunnableParallel(parallel_chain)

        final_res = combined_chain.invoke({})
        return {'final_res':final_res}
    
    def build_retry_map(self,state:ReSummarize) :
        final_res=state['final_res']
        retry_map = {}

        for item_key, item_val in final_res.items():
            details = item_val["final_output"].details
            for i, detail in enumerate(details):
                if detail.summary == "Summary unavailable":
                    markdown = self.app.scrape(str(detail.url)).markdown  
                    task_key = f"{item_key}||{i}"
                    retry_map[task_key] = RunnableLambda(
                        lambda x, d=detail, md=markdown: self.re_summarize(d, md)
                    )

        return {'retry_map':retry_map}
    
    def execute_retry(self,state:ReSummarize):
        retry_map=state['retry_map']
        final_res=state['final_res']

        if retry_map:
            retry_results = RunnableParallel(retry_map).invoke({})

            for task_key, updated_entity in retry_results.items():
                item_key, idx_str = task_key.split("||")
                final_res[item_key]["final_output"].details[int(idx_str)] = updated_entity

        return {'final_res':final_res}
    

    def build_final_workflow(self):
        graph2 = StateGraph(ReSummarize)

        graph2.add_node("run_workflow",self.run_parallel_workflow)
        graph2.add_node('build_retry_map',self.build_retry_map)
        graph2.add_node('execute_retry',self.execute_retry)

        graph2.add_edge(START,"run_workflow")
        graph2.add_edge("run_workflow","build_retry_map")
        graph2.add_edge("build_retry_map","execute_retry")
        graph2.add_edge("execute_retry",END)

        workflow2=graph2.compile()

        return workflow2

    