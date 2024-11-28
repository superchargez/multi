def create_prompt(content:str, page_num:int) -> str:
    prompt = f"""
    Analyze the following markdown content from page {page_num} of a document:

    {content}

    Provide a valid JSON response with the following keys:
    1. "relevant": Mark the content Relevant or NOT Relevant based on given criterion below
        Content or page is relevant as long as it has any information about some sporting event.
        So mark 
    2. "event_info": Information about name, date, frequency, location of event
        2a. "event_info":
            // 2.b
            "event_name": "string", // if provided otherwise skip this
            // 2.c
            "event_date": date, // if provided in content otherwise don't include it
            // 2.d
            "frequency": "string", // if it can't be infered then skip this info from output
            //2.e
            "location": "string" //if location is provided
    3. "metrics": Metrics related to financial, non-financial, qualitative, quantative statistics provided in markdown content
        3a. "metric_name": appropriate name of metric
        3b. "minValue": minimum value (or provided value) of metric
        3c. "maxValue": max value of metric if provided i.e. if provided values are a range
        3d. "valueType" "Estimated"
        3d1. "symbol": if value appears to be currency then make sure it is 3 characters for example USD, SRD etc.
        3e. "magnitude": if value is huge and there is a chance of missing out full value like 1.3 billion dollars then write minValue: 1.3 and magnitude B
    
    Important Notes:
        1. Note that a page may have multiple events, in this case put metrics under their respective event. For example if you encounter following information:
        Economic Impact of Sports Events
        - **Grand Prix**: $350M
        - **World Champs**: $250M
        - **Marathon**: $200M
        present it as follows:
        events: <event name = grand prix>; metrics: <metric name = economic impact>; mivValue: 350; maxValue:350; valueType:Estimated; symbol:$, mag: M ... similarly for other events. Note you will be using braces for json output though I used angle brackets.
        2. A page may have multiple sections, each section may contain information regarding an event or even multiple events, please use the most appropriate method to extract information in such situation and present output json as nested json like this:
        <section>: events <event 1>; metrics: <metric 1>; value, type, etc, <event 2>; similarly do that for all events section-wise.
        2a. Similarly if a page contains multiple sections but each section contains only one event then output json will be less nested i.e. <section> will not be mentioned this way
        3. If a page contains multiple sections for an event then present each section as category and put metrics under its respective category for example if you encounter event information like following:
        # FIS Alpine World Ski Championship 2017

## Event Details
- **Sport:** Skiing - Alpine
- **Owner:** International Ski Federation
- **Date:** 06 Feb - 19 Feb
- **Event Frequency:** Every 2 years
- **Organiser:** Sportsekretariat St. Moritz
- **City, Nation:** St. Moritz - Switzerland

## 2017 GSI Ranking
- **Ranking:** 14th out of 80 events
- **Points:** 1,974 pts

## GSI Event Rating Breakdown
- **Economic & Tourism:** 63%
- **Media & Sponsorship:** 13%
- **Social & Sustainability:** 9%
- **Sporting:** 15%

        then output json should look something like this:
        event info: <event name, date, location etc>; metrics <GSI ranking>; metric_name <ranking>, minValue <14>, other keys according to format. metric_name <points>, minValue <1974> ... other keys accoridng to format for the metric. SI Rating Break Down; metric_name <Economic & Tourism>, minValue <63>, valueType <Estimated> ...etc
        Do this for all the metrics, leave no metric behind.
        4. If you encounter information that can be brokendown further please always break it down to smallest part so that the most appropriate metric can be extracted. For example if you see something like following:
        ### Sporting
- **Athletes - Total:** 488
  - **Men / Women:** 289 / 199
- **Overseas / Domestic:** 463 / 25

From above example it is clear that these values belong to sporting section of page, which can further be broken down to its constituents of athletess so your output should be someting like this:
        sporting: athletes: metric_name <athletes total>, minValue <488>, valueType <Estimated>; metric_name <Men Athletes>, minValue <289>, valueType <"Estimated"> ... metric_name <Domestic Athletes>, minValue <25>
        Please note that there maybe other sections of page with different constituents that need to be broken down like this.
        5. If page has infomration on competing countries or the event or information on future/past events then please include that in output json as well. For example
        input:
        ## Competing Nations By Continent
- **America:** 5
- **Europe:** 47
- **Africa:** 2
    Output:
        Competing Nations by Continent: metric_name <competing nations America>, minValue <5>, valueType <"Estimated"> etc for others in this section.
    If past/future events are mentioned then treat them as normal event just extract as much information from them as possible, mostly there will be information about their location and date, put this information in json according to above format.

                It is important to use the most appropriate keyword as metric name. Please look for whole content to see what is the most appropriate keyword and usually a metric name should not contain event name, date, location.
    Ensure the output is a valid JSON object.
    """
    return prompt

        # 3d. "valueType": [currency, number, string, percentage, null]
        # 3d1. "symbol": if 3d above is a currency then include this with appropriate currency symbol
def create_promptOLD(content:str, page_num:int) -> str:
    prompt = f"""
    Analyze the following markdown content from page {page_num} of a document:

    {content}

    Provide a valid JSON response with the following keys:
    1. "relevant": Mark the content Relevant or NOT Relevant based on given criterion below
        Content or page is relevant as long as it has any information about some sporting event.
        So mark 
    2. "event_info": Information about name, date, frequency, location of event
        2a. "event_info":
            // 2.b
            "event_name": "string", // if provided otherwise skip this
            // 2.c
            "event_date": date, // if provided in content otherwise don't include it
            // 2.d
            "frequency": "string", // if it can't be infered then skip this info from output
            //2.e
            "location": "string" //if location is provided
    3. "metrics": Metrics related to financial, non-financial, qualitative, quantative statistics provided in markdown content
        3a. "metric_name": appropriate name of metric
        3b. "minValue": minimum value (or provided value) of metric
        3c. "maxValue": max value of metric if provided i.e. if provided values are a range
        3d. "valueType" "Estimated"
        3d1. "symbol": if value appears to be currency then make sure it is 3 characters for example USD, SRD etc.
        3e. "magnitude": if value is huge and there is a chance of missing out full value like 1.3 billion dollars then write minValue: 1.3 and magnitude B
    
    Important Notes:
        1. Note that a page may have multiple events, in this case put metrics under their respective event. For example if you encounter following information:
        Economic Impact of Sports Events
        - **Grand Prix**: $350M
        - **World Champs**: $250M
        - **Marathon**: $200M
        present it as follows:
        events: <event name = grand prix>; metrics: <metric name = economic impact>; mivValue: 350; maxValue:350; valueType:currency; symbol:$, mag: M ... similarly for other events. Note you will be using braces for json output though I used angle brackets.
        2. A page may have multiple sections, each section may contain information regarding an event or even multiple events, please use the most appropriate method to extract information in such situation and present output json as nested json like this:
        <section>: events <event 1>; metrics: <metric 1>; value, type, etc, <event 2>; similarly do that for all events section-wise.
        2a. Similarly if a page contains multiple sections but each section contains only one event then output json will be less nested i.e. <section> will not be mentioned this way
        3. If a page contains multiple sections for an event then present each section as category and put metrics under its respective category for example if you encounter event information like following:
        # FIS Alpine World Ski Championship 2017

## Event Details
- **Sport:** Skiing - Alpine
- **Owner:** International Ski Federation
- **Date:** 06 Feb - 19 Feb
- **Event Frequency:** Every 2 years
- **Organiser:** Sportsekretariat St. Moritz
- **City, Nation:** St. Moritz - Switzerland

## 2017 GSI Ranking
- **Ranking:** 14th out of 80 events
- **Points:** 1,974 pts

## GSI Event Rating Breakdown
- **Economic & Tourism:** 63%
- **Media & Sponsorship:** 13%
- **Social & Sustainability:** 9%
- **Sporting:** 15%

        then output json should look something like this:
        event info: <event name, date, location etc>; metrics <GSI ranking>; metric_name <ranking>, minValue <14>, other keys according to format. metric_name <points>, minValue <1974> ... other keys accoridng to format for the metric. SI Rating Break Down; metric_name <Economic & Tourism>, minValue <63>, valueType <percentage> ...etc
        Do this for all the metrics, leave no metric behind.
        4. If you encounter information that can be brokendown further please always break it down to smallest part so that the most appropriate metric can be extracted. For example if you see something like following:
        ### Sporting
- **Athletes - Total:** 488
  - **Men / Women:** 289 / 199
- **Overseas / Domestic:** 463 / 25

From above example it is clear that these values belong to sporting section of page, which can further be broken down to its constituents of athletess so your output should be someting like this:
        sporting: athletes: metric_name <athletes total>, minValue <488>, valueType <number>; metric_name <Men Athletes>, minValue <289>, valueType <num> ... metric_name <Domestic Athletes>, minValue <25>
        Please note that there maybe other sections of page with different constituents that need to be broken down like this.
        5. If page has infomration on competing countries or the event or information on future/past events then please include that in output json as well. For example
        input:
        ## Competing Nations By Continent
- **America:** 5
- **Europe:** 47
- **Africa:** 2
    Output:
        Competing Nations by Continent: metric_name <competing nations America>, minValue <5>, valueType <number> etc for others in this section.
    If past/future events are mentioned then treat them as normal event just extract as much information from them as possible, mostly there will be information about their location and date, put this information in json according to above format.

                It is important to use the most appropriate keyword as metric name. Please look for whole content to see what is the most appropriate keyword and usually a metric name should not contain event name, date, location.
    Ensure the output is a valid JSON object.
    """
    return prompt