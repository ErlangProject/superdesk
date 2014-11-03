import json
import os
import superdesk
import logging
from superdesk import get_resource_service


logger = logging.getLogger(__name__)


def populate_vocabularies(filepath):
    """
    This function upserts the vocabularies into the vocabularies collections.
    The format of the file used is JSON.
    :param filepath: absolute filepath
    :return: nothing
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError

    with open(filepath, 'rt') as vocabularies:
        json_data = json.loads(vocabularies.read())
        service = get_resource_service('vocabularies')

        for item in json_data:
            id_name = item.get("_id")
            try:
                if service.find_one(_id=id_name, req=None):
                    service.put(id_name, item)
                else:
                    service.post(item)
            except Exception as e:
                print('Exception:', e)
                logger.exception("Failed ")


class VocabulariesPopulateCommand(superdesk.Command):
    """
    Class defining the populate vocabularies command.
    """
    option_list = (
        superdesk.Option('--filepath', '-f', dest='filepath', required=True),
    )

    def run(self, filepath):
        populate_vocabularies(filepath)


superdesk.command('vocabularies:populate', VocabulariesPopulateCommand())

