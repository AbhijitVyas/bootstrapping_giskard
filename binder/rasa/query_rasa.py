import ipywidgets as widgets
from IPython.display import display
import json
import requests
import sys
import os
from scripts.preprocessors import preprocessing
from scripts.postprocessings import postprocess
from scripts.intents import Intent

RASA_parse = {}
out = widgets.Output()

# Define a function that will be called when the button is clicked
def handle_submit(sender):
    out.clear_output()
    with out:
        print("You Entered:", text.value)
    preoutput = preprocessing(text.value)

    try:
        payload = {"sender": "Rasa", "text": text.value}
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:5005/model/parse', json=payload, headers=headers)
        rasa_output = response.json()
    except:
        with out:
            print('RASA Connection Failed !!! Try Restarting RASA Server')
            return
    
    text.value = ""
        
    intents = rasa_output['intent']['name']
    final = postprocess(rasa_output,preoutput)

    output = final.print_params()

    RASA_parse['intent'] = intents
    if intents == Intent.POURING:
        RASA_parse['source'] = output['source']
        RASA_parse['destination'] = output['destination']
        RASA_parse['substance'] = output['substance']
        RASA_parse['amount'] = output['amount']
        RASA_parse['units'] = output['units']
        RASA_parse['motion'] = output['motion']
        RASA_parse['action_verb'] = output['action_verb']
        RASA_parse['goal'] = output['goal']
    elif intents == Intent.CUTTING:
        RASA_parse['cutter'] = output['cutter']
        RASA_parse['cuttie'] = output['cuttie']

    with out:
        print("Instruction Info: ", RASA_parse)
    
# Create a text input widget
text = widgets.Text(description="Enter NL Instruction:", layout=widgets.Layout(width='400px'))
text.style.description_width = 'auto'

# Create a button widget
button = widgets.Button(description="Submit")

# Attach the handle_submit function to the button's click event
button.on_click(handle_submit)

# Display the widgets
display(text)
display(button)
display(out)
