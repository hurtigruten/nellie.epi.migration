# HTML to Rich Text Converter

### Usage

`npm i`

`npm start`

The application will run by default at `http://localhost:3000`

### HTML to Rich text example

`POST http://localhost:3000/convert`

Example payload for JSON body:

```json
{
	"from": "html",
	"to": "richtext",
	"html": "<ul>\n<li>Voyage in the cabin category of your choice, on a full-board basis</li>\n<li>English-speaking tour leader on board</li>\n</ul>\n<h3>Engaging onboard activities and lectures:</h3>\n<ul>\n<li>Onboard lectures and presentations on history, biology, geography, geology, and culture&nbsp;that provide context to your voyage&nbsp;and help you understand the destinations you will experience&nbsp;&nbsp;</li>\n<li>Introductory photo presentations, camera adjustment, and tips &amp; tricks, as well as photo and film footage from the voyage</li>\n<li>Opportunities to casually engage with the Hurtigruten guides and other guests,&nbsp;including a&nbsp;welcome&nbsp;event,&nbsp;and daily&nbsp;gatherings&nbsp;to recap the day and prepare for the day to come</li>\n<li>Port&nbsp;presentations&nbsp;providing destination insight</li>\n<li>Excursion presentations</li>\n<li>Point of interest presentations out on deck</li>\n<li>Loan of trekking poles, snowshoes, head lamps, and crampons needed for optional hikes depending on the season and conditions</li>\n<li>Captain&rsquo;s dinner and a&nbsp;farewell event&nbsp;&nbsp;</li>\n</ul>\n<p>&nbsp;</p>"
}
```

This will convert the html to Contentful's Rich Text format. Example response:

```json
{
    "nodeType": "document",
    "data": {},
    "content": [
        {
            "nodeType": "unordered-list",
            "content": [
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Voyage in the cabin category of your choice, on a full-board basis",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "English-speaking tour leader on board",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                }
            ],
            "data": {}
        },
        {
            "nodeType": "heading-3",
            "content": [
                {
                    "nodeType": "text",
                    "value": "Engaging onboard activities and lectures:",
                    "marks": [],
                    "data": {}
                }
            ],
            "data": {}
        },
        {
            "nodeType": "unordered-list",
            "content": [
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Onboard lectures and presentations on history, biology, geography, geology, and culture that provide context to your voyage and help you understand the destinations you will experience  ",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Introductory photo presentations, camera adjustment, and tips & tricks, as well as photo and film footage from the voyage",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Opportunities to casually engage with the Hurtigruten guides and other guests, including a welcome event, and daily gatherings to recap the day and prepare for the day to come",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Port presentations providing destination insight",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Excursion presentations",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Point of interest presentations out on deck",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Loan of trekking poles, snowshoes, head lamps, and crampons needed for optional hikes depending on the season and conditions",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                },
                {
                    "nodeType": "list-item",
                    "content": [
                        {
                            "nodeType": "paragraph",
                            "content": [
                                {
                                    "nodeType": "text",
                                    "value": "Captain's dinner and a farewell event",
                                    "marks": [],
                                    "data": {}
                                }
                            ],
                            "data": {}
                        }
                    ],
                    "data": {}
                }
            ],
            "data": {}
        }
    ]
}
```