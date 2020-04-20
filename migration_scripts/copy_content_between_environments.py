import config
import helpers
import logging
from argparse import ArgumentParser

logging.basicConfig(
    format = '%(asctime)s %(levelname)-8s %(message)s',
    level = logging.INFO,
    datefmt = '%Y-%m-%d %H:%M:%S')

def prepare_environment(environment):
    logging.info('Setup Contentful environment')
    contentful_environment = helpers.create_contentful_environment(
        config.CTFL_SPACE_ID,
        environment,
        config.CTFL_MGMT_API_KEY)

    logging.info('Environment setup: %s' % environment)

    return contentful_environment


if __name__ == '__main__':

    source_environment = prepare_environment('master')

    destination_environment = prepare_environment('locale-for-apac-launch')
    destination_environment.default_locale = 'en'

    entries = helpers.get_all_entries_for_content_type(source_environment, 'usp', 1000, 1000).find('usp53236-1')

    for entry in entries:

        logging.info('Updating entry: %s' % entry.id)

        destination_entry = helpers.get_entry(destination_environment, entry.id)

        try:
            destination_entry.text = entry.fields('en-US')['text']
            destination_entry.save()
            logging.info('Entry updated: %s' % entry.id)
        except Exception as e:
            logging.info('Could not update entry with ID: %s, error: %s' % (entry.id, e))

        try:
            destination_entry.publish()
        except Exception as e:
            logging.info('Could not publish entry with ID: , error: %s' % e)
