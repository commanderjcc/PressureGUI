import pandas as pd
import json


def apply_changes(data, changes):
    """
        Applies the values of changes to data by matching on datetime
    :param data: dataframe to be changed
    :param changes: dataframe with changes to be applied
    :return: updated dataframe
    """
    bool_selection = data['datetime'].isin(changes['datetime'])
    changed_data = data.loc[bool_selection]["pressure_hobo"].add(changes["pressure_hobo"].values)

    data.update(changed_data)

    return data


def log_changes(history, type, changes_df, description):
    """
        Logs a change to the history log

    :param history: json string or list of the history log
    :param type: type of change
    :param changes_df: dataframe with the changes
    :param description: text description of the change
    :return: updated history log
    """
    newChange = Change(des=description, type=type, changes_df=changes_df)  # create a new change object

    if isinstance(history, str):  # if history is a string, parse it into a list
        try:
            history = json.loads(history)
        except:
            print("ERROR: couldn't parse json history string, save your work and run while you still can")

    history.append(newChange.to_json())  # append the new change to the history log
    return history  # return the updated history log (list of change objects)


def undo_delete(data, changes):
    """
        Undoes a delete change by adding the changes back to the data
    :param data:
    :param changes:
    :return:
    """

    data = pd.read_json(data)  # convert data to a dataframe #TODO is this necessary? does the changes var need this?
    return pd.concat([data, changes], join="inner")  # TODO is join inner really necessary?


def undo_shift(data, changes):
    """
        Undoes a shift change by shifting the data in the opposite direction
    :param data:  a dataframe with the data to be undone
    :param changes:  a dataframe with the shifts to be undone
    :return: a dataframe with the changes undone
    """
    data = pd.read_json(data)  # convert data to a dataframe
    changes.pressure_hobo *= -1  # invert the changes
    return apply_changes(data, changes)  # return the data after applying the inverted changes


def undo_add(data, changes):
    """
        !!! UNIMPLEMENTED !!! Undoes an add change by deleting the changes from the data
    """
    pass


class Change:
    """
        A class to represent a change to the data

        Attributes
        ----------
        description : str
            Text description of the change
        type : str
            Type of change corresponds to how the change was made: eg. Delete, Shift, Expcomp, etc.
        undoFunc : function
            A function that we can call to undo this change (eg. undo_delete, undo_shift, etc.)
        changes_df : pandas.DataFrame
            A data frame with the affected changes

        Methods
        -------
        to_json()
            Returns a json string representation of the change
    """
    # Text description of the change
    description = "description uninitialized"

    # Type of change corresponds to how the change was made: eg. Delete, Shift, Expcomp, etc.
    type = ""

    # A function that we can call to undo this change
    undoFunc = None

    # A data frame with the affected changes
    changes_df = pd.DataFrame

    def __init__(self, jsonIn='', des='', type='', changes_df=''):
        if jsonIn != '':  # if we are initializing from a json string
            data = json.loads(jsonIn)  # parse the json string
            self.changes_df = pd.read_json(data['changes_df'])  # convert the changes_df to a dataframe
            self.description = data['description']  # set the description
            self.type = data['type']  # set the type
        else:
            self.description = des  # set the description
            self.type = type  # set the type
            self.changes_df = changes_df  # set the changes_df

        match self.type:
            case "delete":  # if the type is delete
                self.undoFunc = undo_delete  # set the undo function to undo_delete

            case "shift":  # if the type is shift
                self.undoFunc = undo_shift  # set the undo function to undo_shift
            case "compression":  # if the type is compression
                self.undoFunc = undo_shift  # set the undo function to undo_shift

            case "add":  # if the type is add
                self.undoFunc = undo_add  # set the undo function to undo_add

    def to_json(self):
        """
            Returns a json string representation of the change
        :return:  json string representation of the change
        """
        export = {
            "changes_df": self.changes_df.to_json(),  # convert the changes_df to a json string
            "description": self.description,  # set the description
            "type": self.type  # set the type
        }  # create a dictionary with the change data

        return json.dumps(export)  # return the dictionary as a json string
