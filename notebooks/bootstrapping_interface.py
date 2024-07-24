#!/usr/bin/env python3
import sys
import os

sys.path.append(os.getcwd() + "/../")
from binder.rasa.scripts.intents import Intent
from binder.rasa.scripts.parse_instruction_rasa import query_rasa
from rosprolog_client import Prolog, atom
from pymongo import MongoClient




class BootstrapInterface:
    """
        Low-level interface to KnowRob, which enables the easy creation of NEEMs in Python.
        It provides bootstrapping predicates that can be used to create a task learning experience between teacher and a robot student
        """

    def __init__(self, mongo_interface):
        self.prolog = Prolog()
        self.mongo_interface = mongo_interface

    """
    * task_request: here the task request can be natural language sentence, we will parse this sentece and create a skill definition from it.
    * this method will have an interface will mongo skill collection which it will query to get the skill and plan from it.
    """

    def request(self, task_reqest: str):
        # Send the task request to RASA and get back the action core representation, and take action_verb and substance out and create a skill definition.
        action_core = query_rasa(task_reqest)
        if action_core:
            action_core['instruction'] = task_reqest

            # try to find skill with the keywords
            skills_found = self.find_skills(action_verb=action_core['action_verb'], goal=action_core['goal'])
            if not skills_found:
                response = "Sorry, I do not know how to " + action_core['goal'] + ". Can you show me how to do this?"
                print(response)
            return skills_found, action_core
        return None, None

    """
    """

    def save_action_core_to_db(self, action_core):
        # add action core to the mongodb skill collection
        document = self.mongo_interface.collection.insert_one(action_core)
        # Print the inserted document's ID
        print("Document inserted with ID:", document.inserted_id)
        return document

    def update_action_core(self, document):
        # Define the filter to find the document to update
        filter = {"_id": document['_id']}  # Example: Update the document with _id equal to 1

        # Define the update operation
        # update = {"$set": {"field_to_update": "new_value"}}  # Example: Update the field "field_to_update"

        # Update the document
        self.mongo_interface.collection.update_one(filter, document)

        print("Document updated successfully.")

    def find_skills(self, action_verb=None, goal=None):
        # Query documents for the specified field
        cursor = self.mongo_interface.collection.find({'action_verb': {'$regex': action_verb}, 'goal': goal})
        documents = []
        for document in cursor:
            if document:
                response = "Yes, I have found skill " + action_verb + " with goal: " + goal + "\n"
                print(response)
                documents.append(document)
        return documents

    def Perform(self, primitives: list):
        # TODO: use this predicate to build task plan, it should connect with giskard primitive motions
        # Create dictionary from list of primitives
        # self.action_core['task_plans'] = [{"primitive": primitive} for primitive in primitives]
        print("Performing task")

    def Explain(self):
        # TODO: use this predicate to explain the concept, it should connect with KG or Wordnet
        print("Explaining task")

    def Advice(self):
        # TODO: use this predicate to provide an advice for given primitive skill, it should connect to giskard and make necessary adjustments
        print("Advising for the task")

    """
        triple can be in the format of {sub: , pred: , obj:}
    """

    def Ask(self, triple: dict):
        # TODO: use this predicate to query the knowledge base from knowrob
        print("Asking the agent")

    def Demonstrate(self):
        # TODO: use this predicate to load VR neem from directory to knowrob
        print("Demonstrating the task to the agent")


class MongoDbInterface:
    def __init__(self):
        # Connect to MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        # Create or access the database
        self.db = self.client['bootstrapping']

        # Create or access the collection
        self.collection = self.db['skills']

class KnowRobInterface(BootstrapInterface):

    def __init__(self):
        self.prolog = Prolog()

    def get_type(self, obj):
        response = Prolog().ensure_once(f"""
                        kb_project([
                            findall([Type],(has_type({atom(obj)}, Type)), Type)
                        ]).
                    """)
        return response


if __name__ == "__main__":
    mi = MongoDbInterface()
    bi = BootstrapInterface(mi)

    # 1. first set the task definition/instruction
    documents_found, action_core = bi.request("cut cucumber with knife")
    print("skills found results: ", documents_found)
    print("rasa output results: ", action_core)

    # documents_found[0]['test'] = 'test'
    # # 2. Prompt user to change the rasa output if needed
    # for updating the document in mongodb one needs to use $set method which requires the field name and value. So think about this first.
    # bi.update_action_core(documents_found[0])

    bi.Perform(["pickup", "putdown"])
    # save rasa output once user agrees with the format
    # bi.add_skill_to_db()

    # testing the knowrob interface
    # ki = KnowRobInterface()
    # response =  ki.get_type('http://knowrob.org/kb/IAI-kitchen.owl#iai_kitchen_fridge_door_block')
    # print(response)
