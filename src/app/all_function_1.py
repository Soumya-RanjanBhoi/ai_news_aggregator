import feedparser
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from firecrawl import Firecrawl
import time
import os
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel
from src.datasource import rss_category_feeds
from src.Structures.pydantic_objects import *
from src.Structures.state_objects import *
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import asyncio
import nest_asyncio  
nest_asyncio.apply()
from langgraph.graph import StateGraph,START,END



class workflow_1_function:
    def __init__(self):
        self.app =Firecrawl(api_key=os.environ.get("FIRECRAWL_API_KEY",""))
        load_dotenv()

    def extract_url(self,state:GeneralState):
        start= time.time()
        category=state['category']
        preference=state['preference']
        end=time.time()

        print(f"extract_url started at {start}, ended at {end}, lasted for {end-start}")
        return {"url":rss_category_feeds[category][preference]}


    def feedparsing(self,url: str) -> list:
        source = url.split(".")[1]
        result = feedparser.parse(url)
        top4_results = result["entries"][0:4]

        top4_data = []
        for res in top4_results:
            title = res["title"]
            href_url = res["links"][0]["href"]
            top4_data.append({
                "title": title,
                "link": href_url
            })

        return [{"source": source, "information": top4_data}]

    def extract_content(self,state:GeneralState):
        start=time.time()
        urls=state['url']
        src_url = []
        for url in urls:
            source = url.split(".")[1]
            src_url.append({"source": source, "url": url})

        parallel_map = {
            item["source"]: RunnableLambda(lambda x, u=item["url"]: self.feedparsing(u))
            for item in src_url
        }
        parallel_chain = RunnableParallel(parallel_map) 
        end=time.time()
        print(f"extract_content started at {start}, ended at {end}, lasted for {end-start}")
        return {"config":parallel_chain.invoke({})}

    def route_for_filter(self,state:GeneralState):
        category= state['category']

        if category == 'Sports':
            return 'Sport'
        elif category=='Finance':
            return 'Finance'
        elif category == 'Tech':
            return 'Tech'
        elif category == 'Science':
            return 'Science'
        elif category == 'Policy':
            return 'Policy'
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
        reraise=True)
    def invoke_with_retry(self,chain, input_data):
        """Invoke a chain with automatic retry on transient HTTP failures"""
        return chain.invoke(input_data)   
    
    def filter_content_finance(self,state:GeneralState) :
        start=time.time()
        config=state['config']
        
        chat_model=ChatMistralAI(model="mistral-large-latest")
        FILTER_PROMPT = """
        You are a sports news curator. Your job is to select the TOP 4 (if possible) most attention-grabbing and engaging news titles from the list below.

        ## Selection Criteria (in order of priority):
        1. **Controversy or Drama** - Fines, bans, doping violations, disciplinary actions, conflicts, match-fixing allegations
        2. **Big Club / Star Player / Team Involvement** - 
            - Football: Real Madrid, Barcelona, Man Utd, Liverpool, Chelsea, PSG, Mbappe, Ronaldo, Messi etc.
            - Cricket: India, Australia, England, Pakistan, Virat Kohli, Rohit Sharma, Ben Stokes etc.
            - Basketball: Lakers, Warriors, Celtics, LeBron James, Stephen Curry, Giannis etc.
            - Hockey: India, Australia, Netherlands, top NHL teams (Maple Leafs, Bruins etc.)
        3. **Urgency or Breaking News** - Transfers, injuries to key players, sackings, surprise selections, last-minute decisions
        4. **Tournament / Season Stakes** - World Cup, Champions League, IPL, NBA Playoffs, Olympics — high-stakes match results or previews
        5. **Emotional Hook** - Player milestones, retirements, comebacks, record breaks, emotional quotes or fan-facing stories

        ## Input News List:
        {news_data}

        ## Instructions:
        - Analyze ALL titles across ALL sources
        - Pick exactly TOP 4 that will grab the most user attention
        - Cover a mix of sports if possible (e.g. not all 4 from football alone)
        - Avoid duplicates (same story from different sources = pick only one)
        - You MUST always include at least 1 India-focused story (cricket, hockey, or Indian athletes) if present in the list
        - You MUST always pick at least 1 story even if none seem particularly interesting — choose the most relevant one available
        - No explanation, no markdown.
        {format_instructions}
        """

        parser=PydanticOutputParser(pydantic_object=FilteredNewsResponse)

        final_template=PromptTemplate(
        template=FILTER_PROMPT,
        input_variables=["news_data"],
        partial_variables={"format_instructions":parser.get_format_instructions()}
        )

        chain = final_template | chat_model | parser 

        result=self.invoke_with_retry(chain, {"news_data":config})
        end=time.time()
        print(f"filter_content_finance started at {start}, ended at {end}, lasted for {end-start}")
        return {"filtered_cnt":result}

    def filter_content_sport(self,state:GeneralState) :
        start=time.time()
        config=state['config']
        
        chat_model=ChatMistralAI(model="mistral-large-latest")
        FILTER_PROMPT = """
        You are a sports news curator. Your job is to select the TOP 4 (if possible) most attention-grabbing and engaging news titles from the list below.

        ## Selection Criteria (in order of priority):
        1. **Controversy or Drama** - Fines, bans, transfers, conflicts
        2. **Big Club / Star Player involvement** - Real Madrid, Chelsea, Liverpool, Man Utd,Barcelona etc.
        3. **Urgency or Breaking News** - Decisions, warnings, surprises
        4. **Emotional Hook** - Quotes, player reactions, fan-facing stories

        ## Input News List:
    {news_data}

    ## Instructions:
    - Analyze ALL titles across ALL sources
    - Pick exactly TOP 4 or less than 4 but not greater than four that will grab the most user attention
    - Avoid duplicates (same story from different sources = pick only one)
    - No explanation, no markdown.
        {format_instructions}
        """

        parser=PydanticOutputParser(pydantic_object=FilteredNewsResponse)

        final_template=PromptTemplate(
        template=FILTER_PROMPT,
        input_variables=["news_data"],
        partial_variables={"format_instructions":parser.get_format_instructions()}
        )

        chain = final_template | chat_model | parser 

        result=self.invoke_with_retry(chain, {"news_data":config})
        end=time.time()
        print(f"filter_content_sport started at {start}, ended at {end}, lasted for {end-start}")
        return {"filtered_cnt":result}

    def filter_content_science(self,state:GeneralState) :
        start=time.time()
        config=state['config']
        
        chat_model=ChatMistralAI(model="mistral-large-latest")
        FILTER_PROMPT = """
        You are a science news curator. Your job is to select the TOP 4 (if possible) most attention-grabbing and engaging news titles from the list below.

        ## Selection Criteria (in order of priority):
        1. **Breakthrough Discoveries** - New cures, vaccines, space discoveries, particle physics findings, climate tipping points
        2. **Big Institution / Mission / Name Involvement** -
            - Biology & Medicine: WHO, NIH, ICMR, FDA, top journals (Nature, Science, Lancet), landmark studies, known researchers
            - Space & Astronomy: NASA, ISRO, ESA, SpaceX, James Webb Telescope, Mars/Moon missions, black holes, exoplanets
            - Physics & Chemistry: CERN, Nobel Prize winners, quantum computing breakthroughs, new elements or materials
            - Environment & Climate: IPCC, UNEP, COP summits, extreme weather events, endangered species, deforestation alerts
        3. **Urgency or Public Impact** - Disease outbreaks, asteroid threats, pollution crises, drug approvals or bans, radiation incidents
        4. **Human or Emotional Hook** - First-ever achievements, stories affecting everyday life, health warnings for common people, extinction news
        5. **India-Focused Developments** - ISRO missions, Indian research breakthroughs, local environmental crises, ICMR findings, Indian scientists

        ## Input News List:
        {news_data}

        ## Instructions:
        - Analyze ALL titles across ALL sources
        - Pick exactly TOP 4 that will grab the most user attention
        - Cover a mix of science categories if possible (e.g. not all 4 from space alone)
        - Avoid duplicates (same story from different sources = pick only one)
        - You MUST always include at least 1 India-focused story (ISRO, Indian research, local environment) if present in the list
        - You MUST always pick at least 1 story even if none seem particularly interesting — choose the most relevant one available
        - No explanation, no markdown.
        {format_instructions}
        """

        parser=PydanticOutputParser(pydantic_object=FilteredNewsResponse)

        final_template=PromptTemplate(
        template=FILTER_PROMPT,
        input_variables=["news_data"],
        partial_variables={"format_instructions":parser.get_format_instructions()}
        )

        chain = final_template | chat_model | parser 

        result=self.invoke_with_retry(chain, {"news_data":config})
        end=time.time()
        print(f"extract_content_science started at {start}, ended at {end}, lasted for {end-start}")
        return {"filtered_cnt":result}



    def filter_content_tech(self,state:GeneralState) :
        start=time.time()
        config=state['config']
        
        chat_model=ChatMistralAI(model="mistral-large-latest")
        FILTER_PROMPT = """
        You are a technology news curator. Your job is to select the TOP 4 (if possible) most attention-grabbing and engaging news titles from the list below.

        ## Selection Criteria (in order of priority):
        1. **Disruption or Controversy** - Layoffs, lawsuits, data breaches, AI bans, app takedowns, antitrust actions, major outages
        2. **Big Company / Product / Figure Involvement** -
            - AI: OpenAI, Google DeepMind, Anthropic, Meta AI, Microsoft Copilot, GPT, Gemini, Claude, Elon Musk, Sam Altman
            - Startup & Business: Y Combinator, unicorn startups, major funding rounds, acquisitions, IPOs, valuations, prominent founders
            - Mobile & Apps: Apple, Google, Samsung, iOS, Android, App Store, Play Store, WhatsApp, Instagram, TikTok, top app launches
            - Cybersecurity: major hacks, ransomware attacks, zero-day exploits, government surveillance, NSA, CERT-In, data leaks
        3. **Urgency or Breaking News** - Product launches, surprise announcements, emergency patches, sudden bans or shutdowns
        4. **India-Focused Developments** - Indian startups (Zomato, Zepto, Meesho etc.), IT sector news (TCS, Infosys, Wipro), 
            government tech policy (Digital India, IT Act), Indian unicorns, CERT-In advisories, homegrown apps
        5. **Emotional or Consumer Hook** - Stories that directly impact everyday users — privacy concerns, price hikes, app changes, 
            device recalls, scam warnings, social media policy shifts

        ## Input News List:
        {news_data}

        ## Instructions:
        - Analyze ALL titles across ALL sources
        - Pick exactly TOP 4 that will grab the most user attention
        - Cover a mix of tech categories if possible (e.g. not all 4 from AI alone)
        - Avoid duplicates (same story from different sources = pick only one)
        - You MUST always include at least 1 India-focused story (Indian startups, IT sector, govt tech policy) if present in the list
        - You MUST always pick at least 1 story even if none seem particularly interesting — choose the most relevant one available
        - No explanation, no markdown.
        {format_instructions}
        """

        parser=PydanticOutputParser(pydantic_object=FilteredNewsResponse)

        final_template=PromptTemplate(
        template=FILTER_PROMPT,
        input_variables=["news_data"],
        partial_variables={"format_instructions":parser.get_format_instructions()}
        )

        chain = final_template | chat_model | parser 

        result=self.invoke_with_retry(chain, {"news_data":config})
        end=time.time()
        print(f"extract_content_tech started at {start}, ended at {end}, lasted for {end-start}")
        return {"filtered_cnt":result}


    def filter_content_policy(self,state:GeneralState) :
        start=time.time()
        config=state['config']
        model=ChatMistralAI(model="mistral-large-latest")
        FILTER_PROMPT = """
        You are a policy and governance news curator. Your job is to select the TOP 4 (if possible) most attention-grabbing and engaging news titles from the list below.

        ## Selection Criteria (in order of priority):
        1. **Controversy or Political Drama** - Scandals, resignations, no-confidence motions, diplomatic fallouts, protests, 
            election controversies, impeachments, policy reversals
        2. **Big Institution / Leader / Body Involvement** -
            - India Policy: PMO, Parliament, Supreme Court, Election Commission, NITI Aayog, RBI, CBI, ED, 
            key ministers (PM Modi, Home Minister, Finance Minister), state elections, landmark bills & amendments
            - USA Policy: White House, Congress, Supreme Court, FBI, CIA, Federal Reserve, President, key senators,
            executive orders, major legislation (budget, healthcare, immigration)
            - International Policy Bodies: United Nations, WHO, WTO, IMF, World Bank, NATO, G20, G7, BRICS, 
            ICC, ASEAN, EU Parliament, major treaties & sanctions
        3. **Urgency or Breaking News** - Election results, emergency declarations, sudden policy reversals,
            surprise appointments or resignations, war declarations, ceasefire announcements
        4. **Cross-Border or Geopolitical Impact** - India-Pakistan, India-China, US-China, Russia-Ukraine, 
            Middle East conflicts, trade wars, sanctions, border disputes, terrorism-related policy
        5. **Citizen or Public Impact Hook** - Policies directly affecting common people — tax changes, 
            reservation policies, subsidies, welfare schemes, visa rule changes, internet shutdowns

        ## Input News List:
        {news_data}

        ## Instructions:
        - Analyze ALL titles across ALL sources
        - Pick exactly TOP 4 that will grab the most user attention
        - Cover a mix of policy categories if possible (e.g. not all 4 from India alone)
        - Avoid duplicates (same story from different sources = pick only one)
        - You MUST always include at least 1 India-focused story (Indian Parliament, Supreme Court, state politics) if present in the list
        - You MUST always prioritize geopolitically sensitive or high-tension stories over routine policy updates
        - You MUST always pick at least 1 story even if none seem particularly interesting — choose the most relevant one available
        - No explanation, no markdown.
        {format_instructions}
        """

        parser=PydanticOutputParser(pydantic_object=FilteredNewsResponse)

        final_template=PromptTemplate(
        template=FILTER_PROMPT,
        input_variables=["news_data"],
        partial_variables={"format_instructions":parser.get_format_instructions()}
        )

        chain = final_template | model | parser 

        result=self.invoke_with_retry(chain, {"news_data":config})
        end=time.time()
        print(f"extract_content_policy started at {start}, ended at {end}, lasted for {end-start}")
        return {"filtered_cnt":result}


    def scrape_and_summarize(self,url,source,chain):
        res=self.app.scrape(url)
        summ= chain.invoke({"text":res.markdown})
        return {
            "source":source,
            "summary":summ.summary
        }

    async def _scrape_and_summarize_one(self,item,chain,semaphore: asyncio.Semaphore,):
        """
        Scrape a single URL and summarise it.
        The semaphore limits how many calls run concurrently so we stay
        within Mistral's rate limit.
        """
        async with semaphore:
            try:

                loop = asyncio.get_event_loop()
                res = await loop.run_in_executor(
                    None,                         
                    lambda: self.app.scrape(item.url),
                )

                summ = await loop.run_in_executor(
                    None,
                    lambda: self.invoke_with_retry(chain, {"text": res.markdown}),
                )

                return item.title, {
                    "source": item.source,
                    "summary": summ.summary,
                }

            except Exception as e:
                print(f"Error summarising '{item.title}': {e}")
                return item.title, {
                    "source": item.source,
                    "summary": "Summary unavailable",
                }

    async def _summarize_all(self,items, chain, max_concurrent: int = 2):
        """Run all scrape+summarise tasks with a concurrency cap."""
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = [
            self._scrape_and_summarize_one(item, chain, semaphore)
            for item in items
        ]
        results = await asyncio.gather(*tasks)
        return dict(results)




    def generate_summary(self,state: GeneralState):
        start=time.time()
        filtered_cnt = state["filtered_cnt"]

        summ_parser = PydanticOutputParser(pydantic_object=SummaryStructure)

        chat_model = ChatMistralAI(model="mistral-small-latest")

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
            input_variables=["text"],
            partial_variables={
                "format_instructions": summ_parser.get_format_instructions()
            },
        )

        chain = summ_prompt | chat_model | summ_parser

        summary_results = asyncio.run(
            self._summarize_all(filtered_cnt.items, chain, max_concurrent=2)
        )
        end=time.time()
        print(f"gen_summary started at {start}, ended at {end}, lasted for {end-start}")
        return {"summary": summary_results}


    def generate_output_indesired_format(self,state: GeneralState):
        category = state['category']
        choice = state['preference']
        filtered_cnt = state['filtered_cnt']
        summary = state['summary']

        details = []
        for item in filtered_cnt.items:
            summ_data = summary.get(item.title, {})
            details.append(FinalResultEntity(
                category=category,
                preference=choice,
                url=item.url,
                source=item.source,
                summary=summ_data.get("summary", "Summary unavailable")
            ))

        return {"final_output": FinalResult(details=details)}
    
    
    def build_workflow(self):
        graph = StateGraph(GeneralState)
        graph.add_node("extract_url",self.extract_url)
        graph.add_node("extract_content",self.extract_content)
        graph.add_node("filter_content_finance",self.filter_content_finance)
        graph.add_node("filter_content_policy",self.filter_content_policy)
        graph.add_node('filter_content_science',self.filter_content_science)
        graph.add_node('filter_content_sport',self.filter_content_sport)
        graph.add_node('filter_content_tech',self.filter_content_tech)
        graph.add_node("generate_summary",self.generate_summary)
        graph.add_node("generate_output_indesired_format",self.generate_output_indesired_format)

        graph.add_edge(START,'extract_url')
        graph.add_edge('extract_url','extract_content')
        graph.add_conditional_edges(
            "extract_content",
            self.route_for_filter,
            {
                "Sport":"filter_content_sport",
                "Science":"filter_content_science",
                "Finance":"filter_content_finance",
                "Policy":"filter_content_policy",
                "Tech":"filter_content_tech"
            }
        )
        graph.add_edge("filter_content_finance",'generate_summary')
        graph.add_edge("filter_content_sport",'generate_summary')
        graph.add_edge("filter_content_tech",'generate_summary')
        graph.add_edge("filter_content_policy",'generate_summary')
        graph.add_edge("filter_content_science",'generate_summary')
        graph.add_edge('generate_summary','generate_output_indesired_format')
        graph.add_edge('generate_output_indesired_format',END)

        workflow=graph.compile()

        return workflow