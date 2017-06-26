# FCC Comment Analysis

This reposity has Python code designed to download FCC data, storing it in an ElasticSearch instance. There's an additional command to tag and analyze the data further.

After a first pass in a Jupyter Notebook, I used Kibana on AWS to do most of my digging.

To install the package and run tests:

```
$ pip install -e .
$ python setup.py test
```

To crawl the comments, make sure you have a server setup, and then run:

```
$ fcc index --endpoint=http://localhost:9200/
```

This will take anywhere from 2-4 hours (or wont' work at all, if the API is down).

To get a smaller subset of comments for testing, add `-g YYYY-MM-DD` to get comments submitted after the specified date:

```
$ fcc index --endpoint=http://localhost:9200/ -g 2017-06-01
```

I then take another pass on the data, appending "analysis" variables to all of the documents. This makes it a lot easier to spot trends in Kibana.

To analyze the comments:

```
$ fcc analyze --endpoint=http://localhost:9200/
```
