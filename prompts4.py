system_prompt1 = """
You are a keen detective and carefully read every detail in images, reading all text and never missout anything and you keep the numbers correctly saved in mind in case they maybe useful.
"""
system_message8 = """
You are a keen detective specializing in analyzing images related to sporting events. You carefully examine every detail in images, read all text accurately, and remember important numbers. Your focus areas include:

1. Event identification (names, dates, frequencies, locations)
2. Economic metrics (revenue, expenditure, attendance)
3. Social impact measurements
4. Environmental effects
5. Infrastructure details
6. Broadcast/media statistics

You will analyze images and determine if they contain information about actual sporting events (excluding promotional events or general discussions about sports). If relevant, you'll extract information according to the guidelines provided below.

Remember to verify all extracted data by re-examining each section of the image to ensure accuracy and completeness.
"""
instruction1 = """
Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there. You are given an image now use your keen oberservations and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
"""
instruction2 = """
Please read the image as it appears, if it has sections then first of all keep them in mind and then specificially read 'Sporting' section and make sure all values you read in it are correct according to image, even if you have to look at the image or the section twice. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there. You are given an image now use your keen oberservations and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
"""
instruction3 = """
Please read the image as it appears, if it has sections then first of all keep them in mind and then specificially read each section separately and make sure all values you read in each section are correct according to image, even if you have to look at the image or the section more than once. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there. You are given an image now use your keen oberservations and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
"""
instruction4 = """
Please read the image as it appears, if it has sections then first of all keep them in mind and then specificially read each section separately and make sure all values you read in each section are correct according to image, even if you have to look at the image or the section more than once. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there. You are given an image now use your keen oberservations and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
Please duly note that sometimes some sections mention America as North America and South America separately, be mindful of this segregation and do not club them both as "America" if image contains them separately then you should too.
"""
instruction5 = """
Please read the image as it appears, if it has sections then first of all keep them in mind and then specificially read each section separately and make sure all values you read in each section are correct according to image, even if you have to look at the image or the section more than once. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there. You are given an image now use your keen oberservations and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
Please duly note that sometimes some sections mention America as North America and South America separately, be mindful of this segregation and do not club them both as "America" if image contains them separately then you should too. In some images section "Competing Nations By Continent" is North America is separately mentioned then South America, though both may have same value but you should keep them separate if they are mentioned in image like that i.e. separately.
"""
instruction6 = """
Please read the image as it appears, if it has sections then list them all in your mind and then specificially read each section separately and make sure all values you read in each section are correct according to image, even if you have to look at the image or the section more than once. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there.
You must read each section from the image again to verify all values have been extracted correclty and nothing was added or missed.
Please note that some datapoints, called metrics, appear multiple times on the image, they may appear in different sections on same image, and if image contains multiple events then each section may appear more than once (as many times as the events) in that case you need to verify that information was not copied form a section to another section for same or differnt event. Ensure that all metrics in a section have been accounted for and none is missing, and nothing is added to a section.
For verification read each section again and match it with values in image.
You are given an image now use your keen oberservations skills and gather all data and put that in markdown file so that further analysis is easy and values can be put in proper json format later.
"""
instruction7 = """
Please read the image as it appears, if it has sections then list them all in your mind and then specificially read each section separately and make sure all values you read in each section are correct according to image, even if you have to look at the image or the section more than once. Do not assume anything about data, if you encounter a place where some value should be there but you did not see any, then put a null value there.
You must read each section from the image again to verify all values have been extracted correclty and nothing was added or missed.
Please note that some datapoints, called metrics, appear multiple times on the image, they may appear in different sections on same image, and if image contains multiple events then each section may appear more than once (as many times as the events) in that case you need to verify that information was not copied form a section to another section for same or differnt event. Ensure that all metrics in a section have been accounted for and none is missing, and nothing is added to a section.
For verification read each section again and match it with values in image.
You are given an image now use your keen oberservations skills and gather all data and put that in a valid json format  so that further analysis is easy and values can be extracted using json methods.
"""
instruction_message8 = """
Please read the image as it appears, listing all sections in your mind before examining each one separately. Verify all values in each section, even if you need to review the image or section multiple times. Do not assume any data; if a value is missing, mark it as null.

After initial extraction, re-read each section to confirm that all metrics have been accounted for and none were added or copied incorrectly. Ensure that all information is consistent across sections and events.

Once you've gathered all data, present it in a valid JSON format for easy analysis and extraction using JSON methods.
"""
user_message8 = """
Analyze this image and determine if it contains information about actual sporting events. If relevant, extract the data according to these guidelines:

1. Indicate relevance with "RELEVANT" or "NOT_RELEVANT".

2. For relevant content, provide extracted data in the following JSON format:

{
    "is_relevant": true,
    "event_id": "string",
    "events": [
        {
            "metrics": {
                "Event Details": {
                    "event_name": "string",
                    "event_date": "string", // only mention if available
                    "frequency": "string", // provided if available
                    "Location": "string"
                },
                "Statistics": {
                    "[CATEGORY_NAME]": { // only if available in provided image otherwise skip this and use metric_name direclty instead of nesting it under category
                        "[METRIC_NAME]": {
                            "metric_name": "[METRIC_NAME]",
                            "value": [VALUE],
                            "category": "[CATEGORY_NAME]",
                            "sub-category": "[SUB_CATEGORY]" // Only include if present
                        }
                    }
                }
            }
        }
    ]
}


3. For combined information of metrics, split them appropriately. Calculate totals where possible and include them at the bottom of the metric section.

4. If multiple events are present, create separate entries for each event in the "events" array.

5. Example of extraction:

Input:
Event Type  Economic Impact
Global Events $40 billion (Olympics), $15 billion (World Cup), $1.7 billion (World Cup)
Major Events  $850 million (Grand Prix Champs), $850 million (World Champs), $200 million (Marathon)
Localized Events  $90 million (E-Prix), $50 million (World Indoors), $50 million (Major Event), $30 million (U20s Champs), $20 million (Finals)

Output:
{
    "is_relevant": true,
    "event_id": "string",
    "events": [
      {
        "metrics": {
          "Event Details": {
            "event_name": "[EVENT_NAME]"
          },
          "Statistics": {
            "[CATEGORY]": {
              "[METRIC_NAME]": {
                "metric_name": "[METRIC_NAME]",
                "value": [VALUE],
                "category": "[CATEGORY]",
                "sub-category": "[SUB-CATEGORY]" // Only include if present
              }
            }
          }
        }
      }
    ]
}

Important notes:
- Include categories and sub-categories only if they appear in the input.
- For nested structures (like bed nights by visitor type), represent them as shown in the Statistics section.
- Always include the "Event Details" section with relevant information.
- Handle missing values appropriately (e.g., null or empty string).

Remember, the goal is to capture the essence of the structure without overwhelming the model with excessive detail. This approach should help balance providing enough guidance with keeping the prompt concise and manageable for most LLMs.

6. For irrelevant content, simply return:

{
    "is_relevant": false
}
"""
user_message9 = """
Analyze this image and determine if it contains information about actual sporting events. If relevant, extract the data according to these guidelines:

1. Indicate relevance with "RELEVANT" or "NOT_RELEVANT".

2. For relevant content, provide extracted data in the following JSON format:

{
    "is_relevant": true,
    "event_id": "string",
    "events": [
        {
            "metrics": {
                "Event Details": {
                    "event_name": "string",
                    "event_date": "string", // only mention if available
                    "frequency": "string", // provided if available
                    "Location": "string"
                },
                "Statistics": {
                    "[CATEGORY_NAME]": {
                        "[SUBCATEGORY_NAME]": {
                            "[METRIC_NAME]": {
                                "metric_name": "[METRIC_NAME]",
                                "value": [VALUE],
                                "category": "[CATEGORY_NAME]",
                                "sub-category": "[SUBCATEGORY_NAME]",
                                "sub-sub-category": "[SUB_SUB_CATEGORY]" // Include if applicable
                            }
                        }
                    }
                }
            }
        }
    ]
}

3. For combined information of metrics, split them appropriately. Calculate totals where possible and include them at the bottom of the metric section.

4. If multiple events are present, create separate entries for each event in the "events" array.

5. Example of extraction:

Input:
### Sporting
- **Athletes - Total:** 488
  - **Men / Women:** 289 / 199
- **Overseas / Domestic:** 463 / 25
- **Continental Reach:** 4
- **Competing Nations:** 74
- **IF Members participating:** 57%
- **Team officials:** 700*
- **Technical officials:** 50*

Output:
{
    "is_relevant": true,
    "event_id": "sporting_event_001",
    "events": [
        {
            "metrics": {
                "Event Details": {
                    "event_name": "Sporting Event"
                },
                "Statistics": {
                    "SPORTING": {
                        "Athletes": {
                            "Total Athletes": {
                                "metric_name": "Total Athletes",
                                "value": 488,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Men Athletes": {
                                "metric_name": "Men Athletes",
                                "value": 289,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Women Athletes": {
                                "metric_name": "Women Athletes",
                                "value": 199,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Overseas Athletes": {
                                "metric_name": "Overseas Athletes",
                                "value": 463,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Domestic Athletes": {
                                "metric_name": "Domestic Athletes",
                                "value": 25,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            }
                        },
                        "Continental Reach": {
                            "metric_name": "Continental Reach",
                            "value": 4,
                            "category": "Statistics",
                            "sub-category": "SPORTING"
                        },
                } // ... other metrics under their appropriate categories
            }
        }
    ]
}

Important notes:
- Include categories, sub-categories, and sub-sub-categories as shown in the example.
- For nested structures (like Athletes), represent them as nested json structure. For example athletes in Sporting section appear like this:
  - **Men / Women:** 289 / 199
- **Overseas / Domestic:** 463 / 25
You are supposed to seperate them like this:
"Athletes": {
                            "Total Athletes": {
                                "metric_name": "Total Athletes",
                                "value": 488,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Men Athletes": {
                                "metric_name": "Men Athletes",
                                "value": 289,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Women Athletes": {
                                "metric_name": "Women Athletes",
                                "value": 199,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Overseas Athletes": {
                                "metric_name": "Overseas Athletes",
                                "value": 463,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            },
                            "Domestic Athletes": {
                                "metric_name": "Domestic Athletes",
                                "value": 25,
                                "category": "Statistics",
                                "sub-category": "SPORTING",
                                "sub-sub-category": "Athletes"
                            }
                        }

- Always include the "Event Details" section with relevant information.
- Handle missing values appropriately (e.g., null or empty string) put a null value when missing values are encountered.

Another example:
Input:
| Event          | Economic Benefit | Event Type       |
|----------------|------------------|------------------|
| Olympics       | $40,000M         | Global Events    |
| World Cup      | $15,000M         | Global Events    |
| World Cup      | $1,700M          | Global Events    |
| Grand Prix     | $350M            | Major Events     |

or Input:
# Economic Benefits of Sports Events

## Global Events
- **Olympics**
  - Economic Benefit: $40,000M
- **World Cup**
  - Economic Benefit: $15,000M
- **World Cup**
  - Economic Benefit: $1,700M

## Major Events
- **Grand Prix**
  - Economic Benefit: $350M

Output:
{
  "is_relevant": true,
  "events": [
        {
          "Event Details": {
            "event_name": "Olympics"
          },
          "metric_name": "Economic Impact",
          "value": 40000
        },
        {
          "Event Details": {
            "event_name": "World Cup"
          },
          "metric_name": "Economic Impact",
          "value": 15000
        },
        {
          "Event Details": {
            "event_name": "World Cup (2nd)"
          },
          "metric_name": "Economic Impact",
          "value": 1700
        } // .. other events
  ]
}


Remember, the goal is to capture the essence of the structure without overwhelming the model with excessive detail. This approach should help balance providing enough guidance with keeping the prompt concise and manageable for most LLMs.

6. For irrelevant content, simply return:

{
    "is_relevant": false
}
"""
user_message10 = """
Analyze this image and determine if it contains information about actual sporting events. If relevant, extract the data according to these guidelines:

1. Indicate relevance with "RELEVANT" or "NOT_RELEVANT".

2. For relevant content, provide extracted data in the following JSON format:

{
    "is_relevant": true,
    "events": [
        {
            "metrics": {
                "Event Details": {
                    "event_name": "string",
                    "event_date": "string", // only mention if available
                    "frequency": "string", // provided if available
                    "Location": "string"
                },
                "Statistics": { // Statistics is name of a category if information in image is presented without mentioning this name then don't write it in output json and place metric directly under "metrics"
                    "[CATEGORY_NAME]": { // only if mentioned in image otherwise don't include in output and place metric_name directly under metrics
                        "[SUBCATEGORY_NAME]": {
                            "[METRIC_NAME]": {
                                "metric_name": "[METRIC_NAME]",
                                "value": [VALUE],
                            }
                        }
                    }
                }
            }
        }
    ]
}
Note that information might be financial or non-financial, qualitative or quantitative, it could also be bool. And 

3. For combined information of metrics, split them appropriately. Calculate totals where possible and include them at the bottom of the metric section.
- For nested structures (like Athletes), represent them as nested json structure. For example athletes in Sporting section/category appear like this:
### Sporting
- **Athletes - Total:** 488
  - **Men / Women:** 289 / 199
- **Overseas / Domestic:** 463 / 25

You are supposed to seperate them like this:
"Sporting": {
    "Athletes": {
                "Total Athletes": {
                    "metric_name": "Total Athletes",
                    "value": 488,
                },
                "Men Athletes": {
                    "metric_name": "Men Athletes",
                    "value": 289,
                },
                "Women Athletes": {
                    "metric_name": "Women Athletes",
                    "value": 199,
                },
                "Overseas Athletes": {
                    "metric_name": "Overseas Athletes",
                    "value": 463,
                },
                "Domestic Athletes": {
                    "metric_name": "Domestic Athletes",
                    "value": 25,
                }
            }
    }

Please note that Athletes in sporting section is not the only section/category that requires format to be nested like this, anywhere you see infomration nested present it like that in your json output.

4. If multiple events are present, create separate entries for each event in the "events" array.

5. Example of extraction:

Input:
| Event          | Economic Benefit | Event Type       |
|----------------|------------------|------------------|
| Olympics       | $40,000M         | Global Events    |
| World Cup      | $15,000M         | Global Events    |
| World Cup      | $1,700M          | Global Events    |
| Grand Prix     | $350M            | Major Events     |

or Input:
# Economic Benefits of Sports Events

## Global Events
- **Olympics**
  - Economic Benefit: $40,000M
- **World Cup**
  - Economic Benefit: $15,000M
- **World Cup**
  - Economic Benefit: $1,700M

## Major Events
- **Grand Prix**
  - Economic Benefit: $350M

Output:
{
  "is_relevant": true,
  "events": [
        {
          "Event Details": {
            "event_name": "Olympics"
          },
          "metric_name": "Economic Impact",
          "value": 40000
        },
        {
          "Event Details": {
            "event_name": "World Cup"
          },
          "metric_name": "Economic Impact",
          "value": 15000
        },
        {
          "Event Details": {
            "event_name": "World Cup (2nd)"
          },
          "metric_name": "Economic Impact",
          "value": 1700
        } // .. other events
  ]
}

Important notes:
- Include categories, sub-categories, and sub-sub-categories as shown in the example.
- Always include the "Event Details" section with relevant information.
- Handle missing values appropriately (e.g., null or empty string) put a null value when missing values are encountered.

Remember, the goal is to capture the essence of the structure without overwhelming the model with excessive detail. This approach should help balance providing enough guidance with keeping the prompt concise and manageable for most LLMs.

6. For irrelevant content, simply return:

{
    "is_relevant": false
}
"""