import json
import os

# this template provide the basic framework for making json generic template
# title - string
# subtitle - string
# image_url - string
# buttons - dictionary of buttons

def generic_template (recipient, title, subtitle, image_url, button):
    data=json.dumps({
      "recipient": {"id": recipient},
      "message": {
        "attachment":{
            "type":"template",
            "payload":{
                "template_type":"generic",
                "elements":[
                    {
                        "title":"Breaking News: Record Thunderstorms",
                        "subtitle":"The local area is due for record thunderstorms over the weekend.",
                        "image_url":"http://www.ptvsports.net/wp-content/uploads/2016/01/55593131465393.56521905dc8eb.png",
                        "buttons":[
                            {
                                "type":"element_share"
                            },
                            {
                                "type":"postback",
                                "title":"Challenge accepted",
                                "payload":"Mother Fucker"
                            }
                        ]
                    }
                ]
            }
        }
      }
    })
