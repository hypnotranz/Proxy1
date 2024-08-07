from elasticsearch import Elasticsearch

# Configure Elasticsearch client
es = Elasticsearch(['http://localhost:9200'])

# Query the logs
response = es.search(
    index='sample-logs',
    body={
        'query': {
            'match_all': {}
        }
    }
)

# Print the results
for hit in response['hits']['hits']:
    print(hit['_source'])
