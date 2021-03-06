# Python
import logging
import time
import requests
# Packages
from django.core.management import BaseCommand
from django.conf import settings
from elasticsearch.exceptions import NotFoundError
import elasticsearch_dsl as es
from elasticsearch_dsl.connections import connections
# Project
from datasets.normalized import models
from datasets.normalized.documents import Activiteit, Locatie, Organisatie


log = logging.getLogger(__name__)


class Command(BaseCommand):

    doc_types = [Activiteit, Locatie, Organisatie]
    index = settings.ELASTIC_INDEX

    def add_arguments(self, parser):
        parser.add_argument(
            '--build',
            action='store_true',
            dest='build_index',
            default=False,
            help='Build elastic index from postgres')

        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete_indexes',
            default=False,
            help='Delete elastic indexes from elastic')

        parser.add_argument(
            '--reindex',
            action='store_true',
            dest='reindex_data',
            default=False,
            help='Reindex all the data to elastic')

    def handle(self, *args, **options):
        start = time.time()

        if options['delete_indexes']:
            self.delete_index()
        elif options['build_index']:
            self.create_index()
        elif options['reindex_data']:
            self.reindex_data()
        else:
            self.stdout.write("Unkown command")

        self.stdout.write(
            "Total Duration: %.2f seconds" % (time.time() - start))

    def __connect_to_elastic(self):
        # Creates a connection to elastic
        connections.create_connection(
            hosts=settings.ELASTIC_SEARCH_HOSTS,
            retry_on_timeout=True,
        )
        return es.Index(self.index)

    def delete_index(self):
        # Deleteing the index
        requests.delete('http://{}/{}'.format(settings.ELASTIC_SEARCH_HOSTS[0], self.index))

    def create_index(self):
        # Creating a a new index and adding
        # mapping to the doc_types
        idx = self.__connect_to_elastic()
        for dt in self.doc_types:
            idx.doc_type(dt)
        idx.create()

    def reindex_data(self):
        """
        This will work for now but needs to replace with a better system after the poc
        with a 'replay' mechanism
        """
        connections.create_connection(
            hosts=settings.ELASTIC_SEARCH_HOSTS,
            retry_on_timeout=True,
        )
        locations = models.Locatie.objects.all()
        actions = models.Activiteit.objects.all()
        organsiations = models.Organisatie.objects.all()
        for dataset in [locations, actions, organsiations]:
            for item in dataset:
                doc = item.create_doc()
                doc.save()
