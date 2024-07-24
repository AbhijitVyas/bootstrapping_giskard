import requests
import sys
import os
sys.path.append(os.getcwd() + "/../")
from binder.rasa.scripts.preprocessors import preprocessing
from binder.rasa.scripts.postprocessings import postprocess
from binder.rasa.scripts.intents import Intent

RASA_parse = {}


# Define a function that will be called when the button is clicked
def query_rasa(instruction):
    preoutput = preprocessing(instruction)

    try:
        payload = {"sender": "Rasa", "text": instruction}
        headers = {'content-type': 'application/json'}
        response = requests.post('http://localhost:5005/model/parse', json=payload, headers=headers)
        rasa_output = response.json()
        print("rasa_output: ", rasa_output)

        # payload = {"sender": "Rasa", "text": instruction}
        # headers = {'content-type': 'application/json'}
        # response = requests.post('http://localhost:5005/model/parse', data=json.dumps({'text': instruction}))
        # result = response.json()

    except:
        print('RASA Connection Failed !!! Try Restarting RASA Server')
        return

    intents = rasa_output['intent']['name']
    final = postprocess(rasa_output, preoutput)

    if final:
        output = final.print_params()

        RASA_parse['intent'] = intents

        RASA_parse['action_verb'] = output['action_verb']
        RASA_parse['goal'] = output['goal']
        RASA_parse['side_effects'] = output['side_effects']
        if intents == Intent.POURING.value:
            RASA_parse['source'] = output['source']
            RASA_parse['destination'] = output['destination']
            RASA_parse['substance'] = output['substance']
            RASA_parse['amount'] = output['amount']
            RASA_parse['units'] = output['units']
            RASA_parse['motion'] = output['motion']
        elif intents == Intent.CUTTING.value:
            RASA_parse['source'] = output['cutter']
            RASA_parse['destination'] = output['cuttie']
            RASA_parse['cutter'] = output['cutter']
            RASA_parse['cuttie'] = output['cuttie']

        return RASA_parse
    return None
    #
    # print("Instruction Info: ", RASA_parse)

#
# query_rasa("pour coffee from bottle to bowl")
